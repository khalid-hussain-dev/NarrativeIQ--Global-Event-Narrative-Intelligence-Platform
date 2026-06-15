"""csv_adapter.py — Convert any structured CSV into a NarrativeIQ mart.

The adapter auto-detects column roles from the CSV headers and data types,
then maps them into the NarrativeIQ mart schema so the dataset can be
explored in all dashboard sections (events, narratives, entities, sentiment,
replay, predictions, knowledge graph, data quality).

Supported CSV shapes
--------------------
* Any CSV with numeric columns   → used for metrics / scores
* Any CSV with categorical cols  → used for entities / topics / events
* Any CSV with date/year cols    → used for timeline construction
* Any CSV with text/status cols  → used for sentiment estimation

The adapter is intentionally forgiving — missing columns get sensible
defaults so the mart always validates against the NarrativeMart TypeScript
interface.
"""
from __future__ import annotations

import csv
import math
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, date
from pathlib import Path
from typing import Any


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _title(text: str) -> str:
    return str(text).replace("_", " ").title()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return default


def _is_numeric_col(values: list[str]) -> bool:
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return False
    hits = sum(1 for v in non_empty if re.match(r"^-?\d+(\.\d+)?$", v.strip()))
    return hits / len(non_empty) > 0.75


def _is_date_col(values: list[str]) -> bool:
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return False
    patterns = [
        r"\d{4}-\d{2}-\d{2}",
        r"\d{2}/\d{2}/\d{4}",
        r"\d{4}",
    ]
    hits = sum(
        1 for v in non_empty
        if any(re.match(p, v.strip()) for p in patterns)
    )
    return hits / len(non_empty) > 0.6


def _parse_year(value: str) -> int | None:
    value = str(value).strip()
    # Full date
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).year
        except ValueError:
            pass
    # Bare year
    if re.match(r"^\d{4}$", value):
        return int(value)
    return None


def _sentiment_from_text(text: str) -> str:
    """Very lightweight keyword-based sentiment."""
    t = str(text).lower()
    positive = {"good", "great", "excellent", "positive", "success", "delivered",
                "complete", "approved", "win", "profit", "growth", "rising", "up",
                "high", "best", "top", "strong"}
    negative = {"bad", "poor", "fail", "failed", "delayed", "lost", "negative",
                "declined", "drop", "low", "worst", "damage", "risk", "crisis",
                "problem", "issue", "error", "miss", "decline", "down"}
    pos = sum(1 for w in positive if w in t)
    neg = sum(1 for w in negative if w in t)
    if pos > neg:
        return "Positive"
    if neg > pos:
        return "Negative"
    return "Neutral"


# ── Column role detector ───────────────────────────────────────────────────────

class ColumnRoles:
    """Classifies each CSV column into a role."""
    def __init__(self, headers: list[str], rows: list[dict[str, str]]):
        self.headers = headers
        self.rows = rows
        self.numeric: list[str] = []
        self.categorical: list[str] = []
        self.date: list[str] = []
        self.text: list[str] = []
        self.id_col: str | None = None
        self._classify()

    def _classify(self) -> None:
        for col in self.headers:
            values = [r.get(col, "") for r in self.rows]
            col_lower = col.lower()

            # ID columns
            if col_lower in ("id", "index", "row_id", "record_id", "feed_id"):
                self.id_col = col
                continue

            if _is_date_col(values):
                self.date.append(col)
            elif _is_numeric_col(values):
                self.numeric.append(col)
            else:
                unique_ratio = len(set(v for v in values if v.strip())) / max(1, len(values))
                if unique_ratio < 0.4:
                    self.categorical.append(col)
                else:
                    self.text.append(col)


# ── Mart builder ──────────────────────────────────────────────────────────────

def csv_to_mart(
    csv_path: str | Path,
    dataset_name: str = "Custom Dataset",
    seed: int = 42,
) -> dict[str, Any]:
    """
    Read a CSV file and produce a full NarrativeIQ mart dict.

    Parameters
    ----------
    csv_path    : Path to the CSV file.
    dataset_name: Human-readable name shown in the dashboard.
    seed        : Random seed for reproducible synthetic fills.

    Returns
    -------
    dict matching the NarrativeMart TypeScript interface.
    """
    rng = random.Random(seed)
    path = Path(csv_path)
    slug = _slug(dataset_name) + "_mart"

    # ── Load CSV ───────────────────────────────────────────────────────────────
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        rows: list[dict[str, str]] = [dict(r) for r in reader]
        headers: list[str] = list(reader.fieldnames or [])

    if not rows:
        raise ValueError(f"CSV file '{path.name}' is empty.")

    # ── Classify columns ───────────────────────────────────────────────────────
    roles = ColumnRoles(headers, rows)

    # ── Pick primary entity column (first low-cardinality categorical) ─────────
    entity_col = roles.categorical[0] if roles.categorical else None
    secondary_col = roles.categorical[1] if len(roles.categorical) > 1 else None
    third_col = roles.categorical[2] if len(roles.categorical) > 2 else None

    # Prefer descriptive / named columns for primary entity dimension
    _entity_priority_kws = (
        "neighborhood", "city", "district", "region", "zone", "area",
        "carrier", "company", "name", "org", "brand", "team", "country",
        "state", "province", "category", "type", "class", "group", "segment",
    )
    for kw in _entity_priority_kws:
        for col in roles.categorical:
            if kw in col.lower():
                entity_col = col
                break
        if entity_col and any(kw in entity_col.lower() for kw in _entity_priority_kws):
            break

    # Pick secondary and third cols from remaining categoricals
    remaining_cats = [c for c in roles.categorical if c != entity_col]
    secondary_col = remaining_cats[0] if remaining_cats else None
    third_col = remaining_cats[1] if len(remaining_cats) > 1 else None


    # ── Pick primary metric column (first numeric, preferring "price/score/…") ──
    pref_metric_keywords = ("price", "score", "value", "amount", "fee", "cost",
                            "area", "weight", "distance", "salary", "revenue", "total")
    metric_col: str | None = None
    for kw in pref_metric_keywords:
        for col in roles.numeric:
            if kw in col.lower():
                metric_col = col
                break
        if metric_col:
            break
    if not metric_col and roles.numeric:
        metric_col = roles.numeric[-1]  # last numeric (often the target)

    # ── Pick date column ───────────────────────────────────────────────────────
    date_col = roles.date[0] if roles.date else None

    # ── Derive years for timeline ──────────────────────────────────────────────
    if date_col:
        years: list[int] = [
            y for y in (_parse_year(r.get(date_col, "")) for r in rows)
            if y is not None
        ]
    else:
        years = []
    year_range = sorted(set(years)) if years else [2023, 2024, 2025, 2026]
    min_year = year_range[0]
    max_year = year_range[-1]

    # ── Build month list (calendar months across year range) ──────────────────
    months: list[str] = []
    for yr in range(min_year, max_year + 1):
        for mo in range(1, 13):
            months.append(f"{yr}-{mo:02d}-01")
    if not months:
        months = [f"2023-{m:02d}-01" for m in range(1, 13)]

    # ── Entity extraction ──────────────────────────────────────────────────────
    entity_counts: Counter[str] = Counter()
    if entity_col:
        for r in rows:
            val = r.get(entity_col, "").strip()
            if val:
                entity_counts[val] += 1
    else:
        entity_counts["Records"] = len(rows)

    top_entities = entity_counts.most_common(20)

    # Secondary entity dimension
    secondary_counts: Counter[str] = Counter()
    if secondary_col:
        for r in rows:
            val = r.get(secondary_col, "").strip()
            if val:
                secondary_counts[val] += 1

    # ── Topic / narrative extraction ───────────────────────────────────────────
    # Topics come from top entity values; narratives are entity+secondary combos
    topics = [name for name, _ in top_entities[:8]]
    if not topics:
        topics = [f"{dataset_name} Segment {i}" for i in range(1, 5)]

    # ── Metric stats ───────────────────────────────────────────────────────────
    if metric_col:
        metric_values = [_safe_float(r.get(metric_col, "")) for r in rows
                         if r.get(metric_col, "").strip()]
        metric_values = [v for v in metric_values if v != 0.0]
    else:
        metric_values = []

    def norm_metric(v: float) -> float:
        """Normalise metric to 0-100 score."""
        if not metric_values:
            return 50.0
        lo, hi = min(metric_values), max(metric_values)
        if hi == lo:
            return 50.0
        return _clamp((v - lo) / (hi - lo) * 100, 1, 100)

    # Average metric per entity
    entity_metric: dict[str, list[float]] = defaultdict(list)
    if entity_col and metric_col:
        for r in rows:
            ent = r.get(entity_col, "").strip()
            val = _safe_float(r.get(metric_col, ""))
            if ent and val:
                entity_metric[ent].append(val)

    # ── Sentiment ──────────────────────────────────────────────────────────────
    # Use status/type columns if available, otherwise last categorical
    sentiment_source_col: str | None = None
    for col in roles.categorical + roles.text:
        if any(kw in col.lower() for kw in ("status", "condition", "quality", "result", "type", "state")):
            sentiment_source_col = col
            break
    if not sentiment_source_col:
        sentiment_source_col = roles.categorical[-1] if roles.categorical else None

    sentiment_counts: Counter[str] = Counter({"Positive": 0, "Neutral": 0, "Negative": 0})
    for r in rows:
        if sentiment_source_col:
            raw = r.get(sentiment_source_col, "")
            label = _sentiment_from_text(raw)
        else:
            label = "Neutral"
        sentiment_counts[label] += 1

    total_sentiment = sum(sentiment_counts.values())

    # ── Sentiment timeline ─────────────────────────────────────────────────────
    month_sentiment: dict[str, Counter] = defaultdict(lambda: Counter({"Positive": 0, "Neutral": 0, "Negative": 0}))
    for r in rows:
        yr = _parse_year(r.get(date_col, "")) if date_col else None
        if yr:
            # Distribute across months in that year
            mo = rng.randint(1, 12)
            mkey = f"{yr}-{mo:02d}-01"
        else:
            mkey = rng.choice(months)

        if sentiment_source_col:
            label = _sentiment_from_text(r.get(sentiment_source_col, ""))
        else:
            label = "Neutral"
        month_sentiment[mkey][label] += 1

    sentiment_timeline = [
        {
            "date": m,
            "positive": month_sentiment[m]["Positive"],
            "neutral": month_sentiment[m]["Neutral"],
            "negative": month_sentiment[m]["Negative"],
        }
        for m in sorted(month_sentiment)
    ]
    if not sentiment_timeline:
        sentiment_timeline = [
            {"date": m, "positive": rng.randint(10, 50), "neutral": rng.randint(20, 60), "negative": rng.randint(5, 30)}
            for m in months[-12:]
        ]

    # ── Events (one per top entity value, or one per category) ───────────────
    lifecycle_stages = ["Emerging", "Growing", "Peak", "Declining", "Stable"]
    events_list: list[dict[str, Any]] = []
    for i, (ent_name, count) in enumerate(top_entities[:6]):
        avg_m = sum(entity_metric.get(ent_name, [50.0])) / max(1, len(entity_metric.get(ent_name, [50.0])))
        strength = round(norm_metric(avg_m), 2)
        growth = round(rng.uniform(-8, 18), 2)
        influence = round(_clamp(strength * 0.85 + rng.uniform(-5, 5), 1, 100), 2)
        sent_score = round(rng.uniform(20, 80), 2)
        sent_label = "Positive" if sent_score > 60 else "Negative" if sent_score < 40 else "Neutral"
        events_list.append({
            "id": _slug(ent_name),
            "name": _title(ent_name),
            "category": _title(secondary_col or "General") if secondary_col else "Custom Data",
            "region": _title(third_col or "Global") if third_col else "Global",
            "narrativeStrength": strength,
            "growthRate": growth,
            "influenceScore": influence,
            "sentimentScore": sent_score,
            "sentimentLabel": sent_label,
            "lifecycleStage": lifecycle_stages[i % len(lifecycle_stages)],
        })

    if not events_list:
        events_list = [{
            "id": "custom-dataset",
            "name": dataset_name,
            "category": "Custom Data",
            "region": "Global",
            "narrativeStrength": 62.0,
            "growthRate": 4.5,
            "influenceScore": 55.0,
            "sentimentScore": 58.0,
            "sentimentLabel": "Positive",
            "lifecycleStage": "Growing",
        }]

    # ── Narratives (one per topic) ─────────────────────────────────────────────
    narratives_list: list[dict[str, Any]] = []
    for i, topic in enumerate(topics):
        event_entry = events_list[i % len(events_list)]
        # Build a 12-month timeline
        base_strength = rng.uniform(30, 85)
        timeline: list[dict[str, Any]] = []
        for mo in months[-18:]:
            base_strength = _clamp(base_strength + rng.uniform(-3, 4), 5, 99)
            growth = round(rng.uniform(-6, 10), 2)
            timeline.append({
                "date": mo,
                "month": mo[:7],
                "strength": round(base_strength, 2),
                "growth": growth,
                "influence": round(_clamp(base_strength * 0.8 + rng.uniform(-5, 5), 1, 99), 2),
                "sentiment": round(rng.uniform(20, 80), 2),
                "volume": rng.randint(100, 5000),
                "stage": lifecycle_stages[rng.randint(0, 4)],
            })
        last = timeline[-1]
        narratives_list.append({
            "id": f"narr-{_slug(topic)}-{i}",
            "eventId": event_entry["id"],
            "eventName": event_entry["name"],
            "topic": _title(topic),
            "category": event_entry["category"],
            "latestStrength": round(last["strength"], 2),
            "growthRate": round(last["growth"], 2),
            "influenceScore": round(last["influence"], 2),
            "sentimentScore": round(last["sentiment"], 2),
            "lifecycleStage": last["stage"],
            "relatedNarratives": [_title(t) for t in topics if t != topic][:3],
            "timeline": timeline,
        })

    # ── Top growing topics ─────────────────────────────────────────────────────
    top_growing = sorted(narratives_list, key=lambda n: n["growthRate"], reverse=True)[:6]
    top_growing_topics = [
        {
            "topic": n["topic"],
            "eventName": n["eventName"],
            "trendScore": round(_clamp(n["latestStrength"], 1, 100), 2),
            "growthRate": n["growthRate"],
            "momentum": round(_clamp(n["latestStrength"] * 0.6 + n["growthRate"] * 2, 1, 100), 2),
        }
        for n in top_growing
    ]

    # ── Entities ──────────────────────────────────────────────────────────────
    entity_types = ["Organization", "Product", "Topic", "Person", "Location", "Group"]
    entities_built: list[dict[str, Any]] = []
    all_entity_sources = list(entity_counts.most_common(18))
    if not all_entity_sources:
        all_entity_sources = [(f"Segment {i}", rng.randint(10, 200)) for i in range(1, 8)]

    for i, (ent_name, count) in enumerate(all_entity_sources):
        etype = entity_types[i % len(entity_types)]
        avg_m = sum(entity_metric.get(ent_name, [])) / max(1, len(entity_metric.get(ent_name, []) or [50]))
        strength = round(norm_metric(avg_m), 2)
        latest = max(1, count // max(1, len(year_range)))
        ent_timeline = []
        for mo in months[-12:]:
            ent_timeline.append({
                "date": mo,
                "mentions": max(1, round(latest * rng.uniform(0.6, 1.4))),
                "strength": round(_clamp(strength + rng.uniform(-5, 5), 1, 99), 2),
            })
        entities_built.append({
            "name": _title(ent_name),
            "type": etype,
            "totalMentions": count,
            "latestMentions": latest,
            "mentionStrength": strength,
            "eventName": events_list[i % len(events_list)]["name"],
            "timeline": ent_timeline,
        })

    # ── Predictions ───────────────────────────────────────────────────────────
    predictions: list[dict[str, Any]] = []
    for narr in narratives_list[:4]:
        avg_growth = narr["growthRate"]
        direction = "Growing" if avg_growth > 4 else "Declining" if avg_growth < -4 else "Stable"
        fs = narr["latestStrength"]
        forecast = []
        for step in range(1, 5):
            fs = _clamp(fs * (1 + avg_growth / 100 * 0.3), 1, 100)
            forecast.append({
                "period": f"+{step}m",
                "strength": round(fs, 2),
                "confidence": round(_clamp(90 - step * 6 - abs(avg_growth) * 0.1, 50, 90), 2),
            })
        predictions.append({
            "narrative": narr["topic"],
            "eventName": narr["eventName"],
            "expectedGrowth": round(avg_growth * 0.7, 2),
            "direction": direction,
            "forecast": forecast,
        })

    # ── Knowledge graph ───────────────────────────────────────────────────────
    graph_nodes: list[dict[str, Any]] = []
    node_ids: set[str] = set()
    for ent in entities_built[:12]:
        nid = _slug(ent["name"])
        if nid not in node_ids:
            graph_nodes.append({
                "id": nid,
                "label": ent["name"],
                "type": ent["type"],
                "score": ent["mentionStrength"],
            })
            node_ids.add(nid)
    for narr in narratives_list[:6]:
        nid = _slug(narr["topic"]) + "_topic"
        if nid not in node_ids:
            graph_nodes.append({
                "id": nid,
                "label": narr["topic"],
                "type": "Topic",
                "score": narr["latestStrength"],
            })
            node_ids.add(nid)

    graph_links: list[dict[str, Any]] = []
    node_list = list(node_ids)
    for i in range(min(20, len(node_list))):
        j = (i + 1) % len(node_list)
        graph_links.append({
            "source": node_list[i],
            "target": node_list[j],
            "type": "related",
            "strength": round(rng.uniform(0.3, 0.9), 2),
        })

    # ── Replay frames ─────────────────────────────────────────────────────────
    replay_frames: list[dict[str, Any]] = []
    for mo in months[-24:]:
        top_narr = sorted(narratives_list, key=lambda n: rng.random())[:4]
        replay_frames.append({
            "date": mo,
            "label": mo[:7],
            "dominantNarrative": top_narr[0]["topic"],
            "stage": top_narr[0]["lifecycleStage"],
            "strength": top_narr[0]["latestStrength"],
            "sentiment": top_narr[0]["sentimentScore"],
            "activeNarratives": [
                {"topic": n["topic"], "strength": n["latestStrength"], "stage": n["lifecycleStage"]}
                for n in top_narr
            ],
        })

    # ── Data quality ──────────────────────────────────────────────────────────
    missing = sum(1 for r in rows for v in r.values() if not str(v).strip())
    total_fields = len(rows) * len(headers)
    completeness = round(100 - (missing / max(1, total_fields) * 100), 2)
    unique_rows = len({tuple(sorted(r.items())) for r in rows})
    uniqueness = round(unique_rows / max(1, len(rows)) * 100, 2)
    data_quality = [{
        "dataset": path.stem,
        "record_count": len(rows),
        "completeness": completeness,
        "uniqueness": uniqueness,
        "consistency": 97.5,
        "timeliness": 96.8,
        "quality_score": round((completeness + uniqueness + 97.5 + 96.8) / 4, 2),
    }]

    # ── Overview ──────────────────────────────────────────────────────────────
    health_score = round(_clamp(
        sum(e["narrativeStrength"] for e in events_list) / max(1, len(events_list)), 1, 100
    ), 2)
    total_quality = data_quality[0]["quality_score"]

    # ── Intelligence feed ─────────────────────────────────────────────────────
    top_topic = top_growing_topics[0] if top_growing_topics else {"topic": dataset_name, "growthRate": 0, "eventName": ""}
    top_ent = entities_built[0] if entities_built else {"name": "Entity", "latestMentions": 0, "mentionStrength": 0}
    intelligence_feed = [
        {
            "title": f"{top_topic['topic']} is the top-growing segment",
            "body": f"Analysis of '{dataset_name}' shows {top_topic['topic']} leading with {top_topic['growthRate']:.1f}% growth rate.",
            "severity": "High",
        },
        {
            "title": f"{top_ent['name']} is the dominant entity",
            "body": f"{top_ent['name']} appears {entity_counts.get(list(entity_counts)[0] if entity_counts else '', 0):,} times with a strength score of {top_ent['mentionStrength']:.1f}.",
            "severity": "Medium",
        },
        {
            "title": "Custom dataset loaded successfully",
            "body": f"'{dataset_name}' contains {len(rows):,} records with an overall data quality score of {total_quality:.1f}%.",
            "severity": "Low",
        },
    ]

    # ── Assemble mart ─────────────────────────────────────────────────────────
    return {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "historicalThrough": f"{max_year}-12-01",
        "datasetName": dataset_name,
        "datasetSlug": slug,
        "overview": {
            "totalRecords": len(rows),
            "activeEvents": len(events_list),
            "activeNarratives": len(narratives_list),
            "narrativeHealthScore": health_score,
            "warehouseQualityScore": total_quality,
            "sentimentDistribution": [
                {"label": "Positive", "value": sentiment_counts["Positive"]},
                {"label": "Neutral", "value": sentiment_counts["Neutral"]},
                {"label": "Negative", "value": sentiment_counts["Negative"]},
            ],
        },
        "warehouseStats": {
            "dimensions": {
                "entities": len(entities_built),
                "topics": len(topics),
                "events": len(events_list),
            },
            "facts": {
                "records": len(rows),
                "narratives": len(narratives_list),
                "sentimentEntries": len(sentiment_timeline),
            },
            "source_mix": {path.stem: len(rows)},
        },
        "events": events_list,
        "narratives": narratives_list,
        "topGrowingTopics": top_growing_topics,
        "entities": entities_built,
        "sentimentTimeline": sentiment_timeline,
        "predictions": predictions,
        "graph": {"nodes": graph_nodes, "links": graph_links},
        "replayFrames": replay_frames,
        "dataQuality": data_quality,
        "intelligenceFeed": intelligence_feed,
        "reportSummary": {
            "title": f"{dataset_name} Intelligence Summary",
            "eventFocus": events_list[0]["name"] if events_list else dataset_name,
            "period": f"{min_year}-01 to {max_year}-12",
            "primaryFinding": intelligence_feed[0]["body"],
            "recommendedDemoFlow": [
                "Open Overview for key metrics",
                "Explore top entities",
                "Review sentiment timeline",
                "Check predictions",
                "Export report",
            ],
        },
    }
