import json
import math
import os
import re
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

def get_db_helpers():
    from app.main import (
        run_database_sql,
        postgres_configured,
        sql_literal,
        sql_json,
        write_audit_log,
        LIVE_TOPIC_SCHEMA,
    )
    return run_database_sql, postgres_configured, sql_literal, sql_json, write_audit_log, LIVE_TOPIC_SCHEMA


def tokenize(value: str) -> set[str]:
    cleaned = "".join(character.lower() if character.isalnum() else " " for character in value)
    stopwords = {"a", "an", "and", "for", "in", "of", "on", "the", "to", "with"}
    return {token for token in cleaned.split() if token and token not in stopwords}


def text_score(query_tokens: set[str], values: list[str]) -> int:
    searchable = tokenize(" ".join(values))
    if not query_tokens:
        return 0
    return len(query_tokens.intersection(searchable)) * 3 + sum(
        1 for token in query_tokens for value in values if token in value.lower()
    )


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def fetch_json(url: str, timeout: int = 4) -> dict[str, Any] | None:
    request = Request(url, headers={"User-Agent": "NarrativeIQ/0.1 academic demo"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def month_back(months_ago: int) -> str:
    today = datetime.utcnow()
    month = today.month - months_ago
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    return f"{year:04d}-{month:02d}"


def sentiment_from_text(value: str) -> tuple[float, str]:
    positive = {
        "best",
        "growth",
        "launch",
        "popular",
        "success",
        "strong",
        "win",
        "wins",
        "new",
        "record",
        "revival",
        "champion",
    }
    negative = {
        "ban",
        "crisis",
        "decline",
        "failed",
        "loss",
        "risk",
        "scandal",
        "drop",
        "concern",
        "lawsuit",
        "cancel",
    }
    tokens = tokenize(value)
    pos = len(tokens.intersection(positive))
    neg = len(tokens.intersection(negative))
    score = round(clamp((pos - neg) / max(5, pos + neg + 2), -1, 1), 3)
    label = "Positive" if score > 0.12 else "Negative" if score < -0.12 else "Neutral"
    return score, label


def wikipedia_topic(query: str) -> dict[str, Any] | None:
    search_url = "https://en.wikipedia.org/w/api.php?" + urlencode(
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": "1",
        }
    )
    search_payload = fetch_json(search_url, timeout=5)
    query_payload = (search_payload or {}).get("query", {})
    results = query_payload.get("search", [])
    if not results:
        return None

    result = results[0]
    title = result["title"]
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='')}"
    summary = fetch_json(summary_url, timeout=5) or {}
    extract = summary.get("extract") or re.sub("<[^<]+?>", "", result.get("snippet", ""))

    return {
        "title": title,
        "extract": extract,
        "totalHits": int(query_payload.get("searchinfo", {}).get("totalhits", 0) or 0),
        "wordCount": int(result.get("wordcount", 0) or 0),
        "pageId": result.get("pageid"),
        "timestamp": result.get("timestamp"),
        "url": summary.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{quote(title)}"),
    }


def gdelt_articles(query: str) -> list[dict[str, Any]]:
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(
        {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": "20",
            "sort": "hybridrel",
        }
    )
    payload = fetch_json(url, timeout=3)
    articles = (payload or {}).get("articles", [])
    return articles if isinstance(articles, list) else []


def google_news_articles(query: str) -> list[dict[str, Any]]:
    url = "https://news.google.com/rss/search?" + urlencode(
        {
            "q": query,
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en",
        }
    )
    request = Request(url, headers={"User-Agent": "NarrativeIQ/0.1 academic demo"})
    try:
        with urlopen(request, timeout=5) as response:
            xml_text = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return []
    articles: list[dict[str, Any]] = []
    from xml.etree import ElementTree
    try:
        root = ElementTree.fromstring(xml_text)
    except Exception:
        return []

    for item in root.findall(".//item")[:20]:
        title = item.findtext("title") or "Untitled news item"
        link = item.findtext("link") or ""
        source = item.find("source")
        source_name = source.text if source is not None and source.text else "Google News"
        pub_date = item.findtext("pubDate") or ""
        seen = ""
        if pub_date:
            try:
                seen = parsedate_to_datetime(pub_date).strftime("%Y%m%d%H%M%S")
            except (TypeError, ValueError):
                seen = pub_date
        articles.append(
            {
                "title": title,
                "url": link,
                "domain": source_name,
                "sourceCountry": "US",
                "seendate": seen,
            }
        )
    return articles


def live_news_articles(query: str) -> list[dict[str, Any]]:
    articles = gdelt_articles(query)
    seen: set[str] = set()
    combined: list[dict[str, Any]] = []
    for article in articles + google_news_articles(query):
        key = str(article.get("url") or article.get("title") or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        combined.append(article)
    return combined[:24]


def extract_live_entities(query: str, wiki: dict[str, Any] | None, articles: list[dict[str, Any]], event_name: str) -> list[dict[str, Any]]:
    candidates: dict[str, int] = {}
    text_blob = " ".join(
        [query, wiki.get("title", "") if wiki else "", wiki.get("extract", "") if wiki else ""]
        + [str(article.get("title", "")) for article in articles[:12]]
        + [str(article.get("domain", "")) for article in articles[:12]]
    )
    for match in re.findall(r"\b[A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*){0,3}", text_blob):
        cleaned = match.strip(" .,-")
        if len(cleaned) >= 3 and cleaned.lower() not in {"the", "this", "that"}:
            candidates[cleaned] = candidates.get(cleaned, 0) + 1

    for article in articles:
        domain = str(article.get("domain") or article.get("sourceCountry") or "").strip()
        if domain:
            candidates[domain] = candidates.get(domain, 0) + 2

    ranked = sorted(candidates.items(), key=lambda item: item[1], reverse=True)[:6]
    if not ranked:
        ranked = [(query, 3), ("Public sources", 2), ("Reference context", 1)]

    return [
        {
            "name": name,
            "type": "Source" if "." in name else "Entity",
            "totalMentions": count * max(3, len(articles) + 1),
            "latestMentions": count,
            "mentionStrength": round(clamp(38 + count * 9 + len(articles), 1, 99), 2),
            "eventName": event_name,
            "timeline": [
                {"date": month_back(index), "mentions": max(1, count + index % 3), "strength": round(clamp(38 + count * 8, 1, 99), 2)}
                for index in range(5, -1, -1)
            ],
        }
        for name, count in ranked
    ]


def live_topic_profile(query: str) -> dict[str, Any] | None:
    wiki = wikipedia_topic(query)
    articles = live_news_articles(query)
    if not wiki and not articles:
        return None

    title = wiki["title"] if wiki else query
    extract = wiki.get("extract", "") if wiki else ""
    article_titles = " ".join(str(article.get("title", "")) for article in articles)
    sentiment_score, sentiment_label = sentiment_from_text(f"{query} {extract} {article_titles}")
    article_count = len(articles)
    news_source_count = len({article.get("domain") or article.get("sourceCountry") for article in articles if article.get("domain") or article.get("sourceCountry")})
    total_hits = int(wiki.get("totalHits", 0) if wiki else 0)
    word_count = int(wiki.get("wordCount", 0) if wiki else 0)
    reference_signals = (1 if wiki else 0) + min(40, max(0, total_hits // 25)) + min(20, max(0, word_count // 180))
    query_tokens = tokenize(query)
    article_relevance = sum(
        max(0, min(8, text_score(query_tokens, [str(article.get("title", "")), str(article.get("domain", ""))])) )
        for article in articles
    )
    news_signals = int(round(clamp(article_relevance * 0.62 + article_count * 0.35 + news_source_count * 1.15, 0, 96)))
    source_count = news_source_count + (1 if wiki else 0)
    total_signals = reference_signals + news_signals

    reference_weight = math.log1p(max(0, reference_signals)) * 7
    news_weight = min(22, math.sqrt(max(0, news_signals)) * 4)
    source_weight = min(20, math.sqrt(max(0, source_count)) * 5)
    popularity_weight = min(10, math.log10(max(1, total_hits)) * 2.6)
    narrative_strength = round(clamp(24 + reference_weight + news_weight + min(12, word_count / 450) + popularity_weight, 1, 96), 2)
    influence_score = round(clamp(22 + source_weight + reference_weight * 0.55 + min(20, news_signals * 1.25) + popularity_weight, 1, 96), 2)
    current_month = time.strftime("%Y%m", time.gmtime())
    recent_article_count = sum(1 for article in articles if str(article.get("seendate", "")).startswith(current_month))
    relevance_density = clamp(article_relevance / max(1, article_count * 8), 0, 1)
    confidence = round(
        clamp(
            36
            + 16 * (1 - math.exp(-reference_signals / 55))
            + 20 * (1 - math.exp(-news_signals / 75))
            + 12 * (1 - math.exp(-source_count / 18))
            + 10 * relevance_density
            + (min(6, math.log1p(max(0, word_count)) / 1.8) if wiki else 0)
            + min(6, recent_article_count * 0.8),
            35,
            96,
        ),
        2,
    )
    lifecycle = "Peak" if news_signals >= 15 or reference_signals >= 32 else "Growing" if news_signals >= 5 or reference_signals >= 12 else "Emerging" if total_signals else "Reference"
    event_name = f"{title} Live Topic"

    monthly_counts: dict[str, int] = {}
    for article in articles:
        seen = str(article.get("seendate", ""))
        if len(seen) >= 6 and seen[:6].isdigit():
            month = f"{seen[:4]}-{seen[4:6]}"
            monthly_counts[month] = monthly_counts.get(month, 0) + 1

    timeline = []
    for index in range(11, -1, -1):
        month = month_back(index)
        count = monthly_counts.get(month, 0)
        baseline = narrative_strength * 0.45 + count * 8
        reference_drift = min(18, reference_signals * 0.28)
        timeline.append(
            {
                "month": month,
                "strength": round(clamp(baseline + reference_drift + (12 - index) * 1.15, 1, 100), 2),
                "influence": round(clamp(influence_score * 0.55 + count * 9 + reference_drift + (12 - index), 1, 100), 2),
                "sentiment": sentiment_score,
            }
        )

    entities = extract_live_entities(query, wiki, articles, event_name)
    # Scale factors per narrative so they always have visually distinct metrics
    # even when the base values are near the 100-unit maximum.
    # Index 0 (Public Attention) = 100%, Index 1 (Background Context) = 72%,
    # Index 2 (Media Coverage) = 52%  — proportional and never collapse.
    _narrative_scales = [1.0, 0.72, 0.52]
    narratives = [
        {
            "id": f"live-{index}-{re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')}",
            "eventId": "live-topic",
            "eventName": event_name,
            "topic": topic,
            "category": "Live Topic",
            "latestStrength": round(clamp(narrative_strength * _narrative_scales[index], 1, 100), 2),
            "growthRate": round(clamp((news_signals * 2.8 + reference_signals * 0.35) * _narrative_scales[index], -40, 100), 2),
            "influenceScore": round(clamp(influence_score * _narrative_scales[index], 1, 100), 2),
            "sentimentScore": round(sentiment_score * _narrative_scales[index], 4),
            "lifecycleStage": lifecycle,
            "relatedNarratives": [],
            "timeline": [
                {
                    "date": f"{point['month']}-01",
                    "month": point["month"],
                    "strength": round(clamp(point["strength"] * _narrative_scales[index], 1, 100), 2),
                    "growth": round((news_signals * 2.2 + reference_signals * 0.28) * _narrative_scales[index], 2),
                    "influence": round(clamp(point["influence"] * _narrative_scales[index], 1, 100), 2),
                    "sentiment": round(point["sentiment"] * _narrative_scales[index], 4),
                    "volume": max(10, int(point["strength"] * 12 * _narrative_scales[index])),
                    "stage": lifecycle,
                }
                for point in timeline
            ],
        }
        for index, topic in enumerate(
            [
                f"{title} Public Attention",
                f"{title} Background Context",
                f"{title} Media Coverage",
            ],
            start=0,
        )
    ]

    total_sentiment = max(120, news_signals * 14 + reference_signals * 4 + 120)
    positive_share = clamp(0.34 + sentiment_score * 0.28, 0.12, 0.72)
    negative_share = clamp(0.24 - sentiment_score * 0.22, 0.08, 0.58)
    neutral_share = max(0.1, 1 - positive_share - negative_share)
    total_share = positive_share + negative_share + neutral_share
    sentiment_distribution = [
        {"label": "Positive", "value": int(total_sentiment * positive_share / total_share), "share": round(positive_share / total_share * 100, 2)},
        {"label": "Neutral", "value": int(total_sentiment * neutral_share / total_share), "share": round(neutral_share / total_share * 100, 2)},
        {"label": "Negative", "value": int(total_sentiment * negative_share / total_share), "share": round(negative_share / total_share * 100, 2)},
    ]

    summary_text = extract[:360] if extract else f"{query} has live public-source references available."
    if len(extract) > 360:
        summary_text += "..."
    summary_text = (
        f"{title}: {summary_text} "
        f"NarrativeIQ found {total_signals} public signals: {reference_signals} reference signals and "
        f"{news_signals} recent news signals across {source_count} source clusters."
    )

    sources = []
    if wiki:
        sources.append(
            {
                "type": "Reference",
                "title": title,
                "url": wiki.get("url"),
                "domain": "wikipedia.org",
                "publishedAt": wiki.get("timestamp"),
            }
        )
    for article in articles[:8]:
        sources.append(
            {
                "type": "News",
                "title": article.get("title") or article.get("url") or "Untitled source",
                "url": article.get("url"),
                "domain": article.get("domain") or article.get("sourceCountry"),
                "publishedAt": article.get("seendate"),
            }
        )

    return {
        "query": query,
        "mode": "live_ingestion",
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summary_text,
        "sourceNote": "Live brief derived from Wikipedia topic context and public news metadata when available. Use Save Brief to persist this snapshot into PostgreSQL.",
        "confidence": confidence,
        "event": {
            "id": "live-topic",
            "name": event_name,
            "category": "Live Topic",
            "region": "Global",
            "narrativeStrength": narrative_strength,
            "growthRate": round(news_signals * 2.8 + reference_signals * 0.35, 2),
            "influenceScore": influence_score,
            "sentimentScore": sentiment_score,
            "sentimentLabel": sentiment_label,
            "lifecycleStage": lifecycle,
        },
        "influenceScore": influence_score,
        "narrativeStrength": narrative_strength,
        "sentimentScore": sentiment_score,
        "sentimentLabel": sentiment_label,
        "lifecycleStage": lifecycle,
        "narratives": narratives,
        "entities": entities,
        "sentimentDistribution": sentiment_distribution,
        "timeline": timeline,
        "evidence": {
            "totalSignals": total_signals,
            "newsSignals": news_signals,
            "referenceSignals": reference_signals,
            "sourceClusters": source_count,
        },
        "sources": sources,
        "relatedTopics": list(dict.fromkeys([title] + [entity["name"] for entity in entities[:5]])),
        "recommendedActions": [
            "Open Graph to compare live entities against the existing warehouse graph.",
            "Use the report export after saving this topic into the warehouse in the next build.",
            "Mention during demo that this is live context plus warehouse analytics, not random static text.",
        ],
    }


def nearest_topic_profile(mart: dict[str, Any], query: str) -> dict[str, Any]:
    query_tokens = tokenize(query)
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for event in mart["events"]:
        scored.append(
            (
                text_score(query_tokens, [event["name"], event["category"], event["region"], event["lifecycleStage"]]),
                "event",
                event,
            )
        )
    for narrative in mart["narratives"]:
        scored.append(
            (
                text_score(query_tokens, [narrative["topic"], narrative["eventName"], narrative["category"], narrative["lifecycleStage"]]),
                "narrative",
                narrative,
            )
        )
    for entity in mart["entities"]:
        scored.append((text_score(query_tokens, [entity["name"], entity["type"], entity["eventName"]]), "entity", entity))

    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best_type, best_item = scored[0]

    if best_score == 0:
        lowered = query.lower()
        if any(keyword in lowered for keyword in ["ai", "artificial", "machine", "data", "software", "education", "technology"]):
            best_item = next(item for item in mart["events"] if item["category"] == "Technology")
            best_type = "event"
        elif any(keyword in lowered for keyword in ["election", "vote", "party", "policy", "government"]):
            best_item = next(item for item in mart["events"] if item["category"] == "Politics")
            best_type = "event"
        elif any(keyword in lowered for keyword in ["cricket", "sport", "match", "world cup"]):
            best_item = next(item for item in mart["events"] if item["category"] == "Sports")
            best_type = "event"
        elif any(keyword in lowered for keyword in ["climate", "flood", "disaster", "relief"]):
            best_item = next(item for item in mart["events"] if item["category"] == "Disasters")
            best_type = "event"
        else:
            best_item = mart["events"][0]
            best_type = "event"

    event_name = best_item.get("eventName") or best_item.get("name")
    event = next((item for item in mart["events"] if item["name"] == event_name), mart["events"][0])
    narratives = [
        item
        for item in mart["narratives"]
        if item["eventName"] == event["name"] or text_score(query_tokens, [item["topic"], item["category"]]) > 0
    ]
    if not narratives:
        narratives = [mart["narratives"][0]]
    narratives = sorted(narratives, key=lambda item: (item["latestStrength"], item["influenceScore"]), reverse=True)[:5]
    top_narrative = narratives[0]
    entities = [
        item
        for item in mart["entities"]
        if item["eventName"] == event["name"] or text_score(query_tokens, [item["name"], item["type"]]) > 0
    ]
    entities = sorted(entities or mart["entities"], key=lambda item: (item["latestMentions"], item["mentionStrength"]), reverse=True)[:6]

    mode = "warehouse_match" if best_score > 0 else "prospective_brief"
    summary = (
        f"{query} maps most strongly to the {event['name']} event cluster. "
        f"The leading related narrative is {top_narrative['topic']} at {top_narrative['lifecycleStage'].lower()} stage, "
        f"with {top_narrative['latestStrength']} strength and {top_narrative['influenceScore']} influence. "
        "This brief is generated from the local warehouse mart, not live external scraping."
    )

    timeline = top_narrative["timeline"][-12:]
    sentiment_total = sum(item["value"] for item in mart["overview"]["sentimentDistribution"]) or 1

    return {
        "query": query,
        "mode": mode,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summary,
        "sourceNote": "Derived from generated warehouse facts and mart aggregates. Live web/source ingestion is a future module.",
        "confidence": 86 if mode == "warehouse_match" else 62,
        "event": event,
        "influenceScore": round(top_narrative["influenceScore"], 2),
        "narrativeStrength": round(top_narrative["latestStrength"], 2),
        "sentimentScore": round(top_narrative["sentimentScore"], 3),
        "sentimentLabel": "Positive"
        if top_narrative["sentimentScore"] > 0.12
        else "Negative"
        if top_narrative["sentimentScore"] < -0.12
        else "Neutral",
        "lifecycleStage": top_narrative["lifecycleStage"],
        "narratives": narratives,
        "entities": entities,
        "sentimentDistribution": [
            {**item, "share": round(item["value"] / sentiment_total * 100, 2)}
            for item in mart["overview"]["sentimentDistribution"]
        ],
        "timeline": [
            {
                "month": item["month"],
                "strength": item["strength"],
                "influence": item["influence"],
                "sentiment": item["sentiment"],
            }
            for item in timeline
        ],
        "relatedTopics": list(dict.fromkeys([item["topic"] for item in narratives] + [item["name"] for item in entities[:3]]))[:8],
        "recommendedActions": [
            "Review related narratives and entities before presenting the topic as a public trend.",
            "Use the knowledge graph to explain influence pathways.",
            "Run live source ingestion before claiming real-world current accuracy.",
        ],
    }


def ensure_live_topic_schema():
    run_database_sql, postgres_configured, sql_literal, sql_json, write_audit_log, LIVE_TOPIC_SCHEMA = get_db_helpers()
    if not LIVE_TOPIC_SCHEMA.exists():
        raise RuntimeError("Live topic warehouse schema file is missing.")
    run_database_sql(LIVE_TOPIC_SCHEMA.read_text(encoding="utf-8"))


def save_topic_brief(brief: dict[str, Any]) -> dict[str, Any]:
    run_database_sql, postgres_configured, sql_literal, sql_json, write_audit_log, LIVE_TOPIC_SCHEMA = get_db_helpers()
    ensure_live_topic_schema()
    evidence = brief.get("evidence") or {}
    event = brief.get("event") or {}
    topic_name = str(brief.get("query") or event.get("name") or "Untitled topic")[:255]
    canonical_title = str(event.get("name") or topic_name).replace(" Live Topic", "")[:255]
    payload = json.loads(json.dumps(brief, ensure_ascii=False))

    def numeric(value: Any, default: float = 0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    insert_sql = f"""
SET search_path TO narrativeiq;
WITH upsert_topic AS (
    INSERT INTO dim_live_topic (topic_name, canonical_title, last_seen_at)
    VALUES ({sql_literal(topic_name)}, {sql_literal(canonical_title)}, NOW())
    ON CONFLICT (topic_name)
    DO UPDATE SET canonical_title = EXCLUDED.canonical_title, last_seen_at = NOW()
    RETURNING topic_key
),
snapshot AS (
    INSERT INTO fact_live_topic_snapshot (
        topic_key,
        mode,
        confidence,
        narrative_strength,
        influence_score,
        sentiment_score,
        sentiment_label,
        lifecycle_stage,
        total_signals,
        news_signals,
        reference_signals,
        source_clusters,
        summary,
        source_note,
        payload
    )
    SELECT
        topic_key,
        {sql_literal(brief.get("mode", "live_ingestion"))},
        {numeric(brief.get("confidence"))},
        {numeric(brief.get("narrativeStrength"))},
        {numeric(brief.get("influenceScore"))},
        {numeric(brief.get("sentimentScore"))},
        {sql_literal(brief.get("sentimentLabel", "Neutral"))},
        {sql_literal(brief.get("lifecycleStage", "Unknown"))},
        {int(numeric(evidence.get("totalSignals")))},
        {int(numeric(evidence.get("newsSignals")))},
        {int(numeric(evidence.get("referenceSignals")))},
        {int(numeric(evidence.get("sourceClusters")))},
        {sql_literal(brief.get("summary", ""))},
        {sql_literal(brief.get("sourceNote", ""))},
        {sql_json(payload)}::jsonb
    FROM upsert_topic
    RETURNING snapshot_key, topic_key
)
SELECT json_build_object('topicKey', topic_key, 'snapshotKey', snapshot_key)::text FROM snapshot;
"""
    output = run_database_sql(insert_sql, extra_args=["-t", "-A"])
    saved = json.loads(output.splitlines()[-1]) if output else {}
    snapshot_key = int(saved["snapshotKey"])

    sources = brief.get("sources") or []
    values = []
    for source in sources[:20]:
        values.append(
            "("
            f"{snapshot_key}, "
            f"{sql_literal(source.get('type', 'Reference'))}, "
            f"{sql_literal(source.get('title', 'Untitled source'))}, "
            f"{sql_literal(source.get('url'))}, "
            f"{sql_literal(source.get('domain'))}, "
            f"{sql_literal(source.get('publishedAt'))}"
            ")"
        )

    if values:
        source_sql = (
            "SET search_path TO narrativeiq;\n"
            "INSERT INTO live_topic_sources "
            "(snapshot_key, source_type, source_title, source_url, source_domain, published_at) VALUES\n"
            + ",\n".join(values)
            + ";"
        )
        run_database_sql(source_sql)

    return {
        "status": "saved",
        "topicKey": int(saved["topicKey"]),
        "snapshotKey": snapshot_key,
        "sourcesSaved": len(values),
    }


def list_saved_topic_briefs(limit: int = 8) -> list[dict[str, Any]]:
    run_database_sql, postgres_configured, sql_literal, sql_json, write_audit_log, LIVE_TOPIC_SCHEMA = get_db_helpers()
    ensure_live_topic_schema()
    safe_limit = max(1, min(25, int(limit)))
    query_sql = f"""
SET search_path TO narrativeiq;
WITH recent AS (
    SELECT
        snapshot.snapshot_key,
        topic.topic_key,
        topic.topic_name,
        topic.canonical_title,
        snapshot.measured_at,
        snapshot.mode,
        snapshot.confidence,
        snapshot.narrative_strength,
        snapshot.influence_score,
        snapshot.sentiment_label,
        snapshot.lifecycle_stage,
        snapshot.total_signals,
        snapshot.news_signals,
        snapshot.reference_signals,
        snapshot.source_clusters,
        snapshot.summary,
        (
            SELECT COUNT(*)
            FROM live_topic_sources source
            WHERE source.snapshot_key = snapshot.snapshot_key
        ) AS sources_saved
    FROM fact_live_topic_snapshot snapshot
    JOIN dim_live_topic topic ON topic.topic_key = snapshot.topic_key
    ORDER BY snapshot.measured_at DESC
    LIMIT {safe_limit}
)
SELECT COALESCE(
    json_agg(
        json_build_object(
            'snapshotKey', snapshot_key,
            'topicKey', topic_key,
            'topicName', topic_name,
            'canonicalTitle', canonical_title,
            'measuredAt', to_char(measured_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
            'mode', mode,
            'confidence', confidence,
            'narrativeStrength', narrative_strength,
            'influenceScore', influence_score,
            'sentimentLabel', sentiment_label,
            'lifecycleStage', lifecycle_stage,
            'totalSignals', total_signals,
            'newsSignals', news_signals,
            'referenceSignals', reference_signals,
            'sourceClusters', source_clusters,
            'sourcesSaved', sources_saved,
            'summary', summary
        )
        ORDER BY measured_at DESC
    ),
    '[]'::json
)::text
FROM recent;
"""
    output = run_database_sql(query_sql, extra_args=["-q", "-t", "-A"])
    return json.loads(output.splitlines()[-1]) if output else []


def saved_topic_brief(snapshot_key: int) -> dict[str, Any]:
    run_database_sql, postgres_configured, sql_literal, sql_json, write_audit_log, LIVE_TOPIC_SCHEMA = get_db_helpers()
    ensure_live_topic_schema()
    query_sql = f"""
SET search_path TO narrativeiq;
WITH selected AS (
    SELECT
        snapshot.snapshot_key,
        topic.topic_key,
        topic.topic_name,
        topic.canonical_title,
        snapshot.measured_at,
        snapshot.mode,
        snapshot.confidence,
        snapshot.narrative_strength,
        snapshot.influence_score,
        snapshot.sentiment_label,
        snapshot.lifecycle_stage,
        snapshot.total_signals,
        snapshot.news_signals,
        snapshot.reference_signals,
        snapshot.source_clusters,
        snapshot.summary,
        snapshot.source_note,
        snapshot.payload
    FROM fact_live_topic_snapshot snapshot
    JOIN dim_live_topic topic ON topic.topic_key = snapshot.topic_key
    WHERE snapshot.snapshot_key = {int(snapshot_key)}
),
source_rows AS (
    SELECT COALESCE(
        json_agg(
            json_build_object(
                'type', source_type,
                'title', source_title,
                'url', source_url,
                'domain', source_domain,
                'publishedAt', published_at
            )
            ORDER BY source_key
        ),
        '[]'::json
    ) AS sources
    FROM live_topic_sources
    WHERE snapshot_key = {int(snapshot_key)}
)
SELECT json_build_object(
    'snapshot',
    json_build_object(
        'snapshotKey', snapshot_key,
        'topicKey', topic_key,
        'topicName', topic_name,
        'canonicalTitle', canonical_title,
        'measuredAt', to_char(measured_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
        'mode', mode,
        'confidence', confidence,
        'narrativeStrength', narrative_strength,
        'influenceScore', influence_score,
        'sentimentLabel', sentiment_label,
        'lifecycleStage', lifecycle_stage,
        'totalSignals', total_signals,
        'newsSignals', news_signals,
        'referenceSignals', reference_signals,
        'sourceClusters', source_clusters,
        'summary', summary,
        'sourceNote', source_note
    ),
    'brief',
    payload,
    'sources',
    source_rows.sources
)::text
FROM selected, source_rows;
"""
    output = run_database_sql(query_sql, extra_args=["-q", "-t", "-A"])
    if not output:
        raise KeyError(f"Saved topic snapshot {snapshot_key} was not found.")
    return json.loads(output.splitlines()[-1])
