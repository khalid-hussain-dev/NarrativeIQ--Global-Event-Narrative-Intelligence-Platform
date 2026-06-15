from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "datasets"
RAW_DIR = DATASETS / "raw"
WAREHOUSE_DIR = DATASETS / "warehouse"
MART_DIR = DATASETS / "marts"
FRONTEND_DATA = ROOT / "frontend" / "src" / "data"
FRONTEND_PUBLIC_DATA = ROOT / "frontend" / "public" / "data"


@dataclass(frozen=True)
class TopicConfig:
    name: str
    category: str
    start_offset: int
    duration: int
    amplitude: int
    sentiment_bias: float


@dataclass(frozen=True)
class EntityConfig:
    name: str
    entity_type: str
    weight: float


@dataclass(frozen=True)
class EventConfig:
    event_id: str
    name: str
    category: str
    region: str
    start_date: str
    end_date: str
    topics: tuple[TopicConfig, ...]
    entities: tuple[EntityConfig, ...]


SOURCES = [
    {"source_id": "news_global", "source_name": "Global Newswire", "source_type": "News", "platform": "Web"},
    {"source_id": "policy_desk", "source_name": "Policy Desk", "source_type": "News", "platform": "Web"},
    {"source_id": "forum_pulse", "source_name": "ForumPulse", "source_type": "Discussion Forum", "platform": "Community"},
    {"source_id": "social_x", "source_name": "X Public Stream", "source_type": "Social", "platform": "X"},
    {"source_id": "reddit_public", "source_name": "Reddit Public Threads", "source_type": "Discussion Forum", "platform": "Reddit"},
    {"source_id": "sportswire", "source_name": "SportsWire", "source_type": "News", "platform": "Web"},
]


EVENTS: tuple[EventConfig, ...] = (
    EventConfig(
        event_id="ai-revolution",
        name="Artificial Intelligence Revolution",
        category="Technology",
        region="Global",
        start_date="2023-01-01",
        end_date="2026-06-01",
        topics=(
            TopicConfig("AI Assistants", "Technology", 0, 18, 3600, 0.22),
            TopicConfig("Multimodal AI", "Technology", 10, 20, 5200, 0.18),
            TopicConfig("AI Agents", "Technology", 20, 18, 7800, 0.14),
            TopicConfig("AI Governance", "Policy", 24, 22, 6400, -0.03),
            TopicConfig("Autonomous AI Systems", "Technology", 34, 18, 8300, 0.07),
        ),
        entities=(
            EntityConfig("OpenAI", "Organization", 1.0),
            EntityConfig("GPT Models", "Product", 0.86),
            EntityConfig("Microsoft", "Organization", 0.68),
            EntityConfig("AI Agents", "Topic", 0.74),
            EntityConfig("Developers", "Group", 0.45),
            EntityConfig("Regulators", "Group", 0.42),
        ),
    ),
    EventConfig(
        event_id="cricket-world-cup",
        name="Cricket World Cup",
        category="Sports",
        region="International",
        start_date="2023-07-01",
        end_date="2026-06-01",
        topics=(
            TopicConfig("Tournament Build Up", "Sports", 6, 12, 4300, 0.20),
            TopicConfig("Pakistan Squad Debate", "Sports", 11, 14, 5200, -0.05),
            TopicConfig("Final Match Fever", "Sports", 14, 8, 7600, 0.24),
            TopicConfig("Broadcast Rights", "Business", 18, 16, 3600, 0.06),
        ),
        entities=(
            EntityConfig("Pakistan Cricket Board", "Organization", 0.78),
            EntityConfig("ICC", "Organization", 0.88),
            EntityConfig("Babar Azam", "Person", 0.82),
            EntityConfig("India", "Location", 0.62),
            EntityConfig("Fans", "Group", 0.55),
        ),
    ),
    EventConfig(
        event_id="global-elections",
        name="Global Elections",
        category="Politics",
        region="Global",
        start_date="2023-09-01",
        end_date="2026-06-01",
        topics=(
            TopicConfig("Election Security", "Politics", 8, 24, 5800, -0.12),
            TopicConfig("Youth Voter Turnout", "Politics", 12, 22, 4100, 0.10),
            TopicConfig("Misinformation Monitoring", "Policy", 16, 20, 6300, -0.18),
            TopicConfig("Coalition Negotiations", "Politics", 24, 16, 5400, -0.03),
        ),
        entities=(
            EntityConfig("Election Commission", "Organization", 0.92),
            EntityConfig("Political Parties", "Organization", 0.78),
            EntityConfig("Civil Society", "Organization", 0.48),
            EntityConfig("Youth Voters", "Group", 0.58),
            EntityConfig("Fact Checkers", "Group", 0.52),
        ),
    ),
    EventConfig(
        event_id="disaster-response",
        name="Natural Disaster Response",
        category="Disasters",
        region="Asia Pacific",
        start_date="2023-03-01",
        end_date="2026-06-01",
        topics=(
            TopicConfig("Flood Relief", "Disaster Response", 2, 16, 4600, -0.08),
            TopicConfig("Emergency Logistics", "Operations", 5, 20, 3900, 0.02),
            TopicConfig("Climate Risk", "Environment", 13, 28, 6200, -0.02),
            TopicConfig("Resilience Funding", "Policy", 24, 20, 3600, 0.05),
        ),
        entities=(
            EntityConfig("Relief Agencies", "Organization", 0.9),
            EntityConfig("Local Communities", "Group", 0.74),
            EntityConfig("Climate Scientists", "Group", 0.48),
            EntityConfig("Government Response Units", "Organization", 0.62),
            EntityConfig("Asia Pacific", "Location", 0.56),
        ),
    ),
)


RELATIONSHIPS = [
    ("OpenAI", "GPT Models", "CREATED", 0.95),
    ("OpenAI", "Microsoft", "PARTNERSHIP", 0.90),
    ("OpenAI", "AI Agents", "INFLUENCED", 0.88),
    ("AI Agents", "Developers", "ADOPTED_BY", 0.72),
    ("AI Governance", "Regulators", "RELATED_TO", 0.82),
    ("Autonomous AI Systems", "AI Governance", "TENSION_WITH", 0.76),
    ("ICC", "Cricket World Cup", "ORGANIZES", 0.93),
    ("Pakistan Cricket Board", "Babar Azam", "REPRESENTS", 0.78),
    ("Election Commission", "Election Security", "GOVERNS", 0.86),
    ("Misinformation Monitoring", "Fact Checkers", "SUPPORTED_BY", 0.81),
    ("Relief Agencies", "Flood Relief", "COORDINATES", 0.87),
    ("Climate Risk", "Resilience Funding", "DRIVES", 0.71),
]


def month_range(start: date, end: date) -> list[date]:
    months: list[date] = []
    current = date(start.year, start.month, 1)
    while current <= end:
        months.append(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return months


def date_key(value: date) -> int:
    return value.year * 10000 + value.month * 100 + value.day


def lifecycle(progress: float) -> str:
    if progress < 0:
        return "Emerging"
    if progress < 0.30:
        return "Emerging"
    if progress < 0.58:
        return "Growing"
    if progress < 0.78:
        return "Peak"
    if progress < 1.05:
        return "Declining"
    return "Archived"


def lifecycle_strength(progress: float) -> float:
    if progress < 0:
        return 0.04
    if progress <= 1:
        return math.sin(progress * math.pi)
    return max(0.10, 0.34 * math.exp(-(progress - 1) * 1.35))


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_narrative_rows(months: list[date], rng: random.Random) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    narrative_rows: list[dict[str, Any]] = []
    sentiment_rows: list[dict[str, Any]] = []
    trend_rows: list[dict[str, Any]] = []
    entity_rows: list[dict[str, Any]] = []

    previous_volume: dict[tuple[str, str], int] = {}

    for event in EVENTS:
        for month_index, month in enumerate(months):
            event_month_volume = 0
            for topic in event.topics:
                progress = (month_index - topic.start_offset) / topic.duration
                curve = lifecycle_strength(progress)
                seasonal = 0.92 + 0.15 * math.sin(month_index / 2.9) + rng.uniform(-0.04, 0.05)
                volume = int(max(35, topic.amplitude * curve * seasonal))
                previous = previous_volume.get((event.event_id, topic.name), max(1, int(volume * 0.72)))
                growth_rate = round(((volume - previous) / max(previous, 1)) * 100, 2)
                previous_volume[(event.event_id, topic.name)] = volume

                sentiment_score = round(clamp(topic.sentiment_bias + 0.18 * math.sin(month_index / 4.2) + rng.uniform(-0.08, 0.08), -0.72, 0.78), 3)
                influence_score = round(clamp((curve * 82) + abs(growth_rate) * 0.11 + rng.uniform(2, 12), 1, 99), 2)
                narrative_strength = round(clamp((volume / topic.amplitude) * 100, 1, 100), 2)
                stage = lifecycle(progress)
                event_month_volume += volume

                narrative_rows.append(
                    {
                        "date": month.isoformat(),
                        "event_id": event.event_id,
                        "event_name": event.name,
                        "topic": topic.name,
                        "topic_category": topic.category,
                        "volume": volume,
                        "sentiment_score": sentiment_score,
                        "growth_rate": growth_rate,
                        "influence_score": influence_score,
                        "narrative_strength": narrative_strength,
                        "lifecycle_stage": stage,
                    }
                )

                pos_share = clamp(0.36 + sentiment_score * 0.34, 0.10, 0.78)
                neg_share = clamp(0.25 - sentiment_score * 0.22, 0.08, 0.62)
                neu_share = clamp(1 - pos_share - neg_share, 0.12, 0.58)
                total_share = pos_share + neg_share + neu_share
                positive = int(volume * pos_share / total_share)
                negative = int(volume * neg_share / total_share)
                neutral = max(0, volume - positive - negative)

                sentiment_rows.append(
                    {
                        "date": month.isoformat(),
                        "event_id": event.event_id,
                        "event_name": event.name,
                        "topic": topic.name,
                        "positive": positive,
                        "neutral": neutral,
                        "negative": negative,
                        "sentiment_score": sentiment_score,
                    }
                )

                trend_rows.append(
                    {
                        "date": month.isoformat(),
                        "event_id": event.event_id,
                        "topic": topic.name,
                        "trend_score": round(clamp(narrative_strength * 0.62 + influence_score * 0.38, 1, 100), 2),
                        "growth_rate": growth_rate,
                        "momentum": round(clamp(growth_rate * 0.45 + narrative_strength * 0.22, -60, 100), 2),
                    }
                )

            for entity in event.entities:
                mention_count = int(event_month_volume * entity.weight * rng.uniform(0.035, 0.065))
                entity_rows.append(
                    {
                        "date": month.isoformat(),
                        "event_id": event.event_id,
                        "event_name": event.name,
                        "entity_name": entity.name,
                        "entity_type": entity.entity_type,
                        "mention_count": max(1, mention_count),
                        "mention_strength": round(clamp(entity.weight * 74 + rng.uniform(4, 22), 1, 99), 2),
                    }
                )

    return narrative_rows, sentiment_rows, trend_rows, entity_rows


def build_dimensions(months: list[date], imported_sources: list[dict[str, Any]] = None) -> dict[str, list[dict[str, Any]]]:
    first_day = months[0]
    last_day = months[-1] + timedelta(days=27)
    dim_date: list[dict[str, Any]] = []
    current = first_day
    while current <= last_day:
        dim_date.append(
            {
                "date_key": date_key(current),
                "full_date": current.isoformat(),
                "day": current.day,
                "week": current.isocalendar().week,
                "month": current.month,
                "quarter": (current.month - 1) // 3 + 1,
                "year": current.year,
            }
        )
        current += timedelta(days=1)

    all_sources = SOURCES + (imported_sources or [])
    dim_source = [
        {
            "source_key": index + 1,
            "source_id": source["source_id"],
            "source_name": source["source_name"],
            "source_type": source["source_type"],
            "platform": source["platform"],
        }
        for index, source in enumerate(all_sources)
    ]

    dim_event = [
        {
            "event_key": index + 1,
            "event_id": event.event_id,
            "event_name": event.name,
            "event_category": event.category,
            "region": event.region,
            "start_date": event.start_date,
            "end_date": event.end_date,
        }
        for index, event in enumerate(EVENTS)
    ]

    topics: list[tuple[str, str]] = []
    for event in EVENTS:
        for topic in event.topics:
            if (topic.name, topic.category) not in topics:
                topics.append((topic.name, topic.category))

    dim_topic = [
        {
            "topic_key": index + 1,
            "topic_name": topic,
            "topic_category": category,
        }
        for index, (topic, category) in enumerate(topics)
    ]

    entities: list[tuple[str, str]] = []
    for event in EVENTS:
        for entity in event.entities:
            if (entity.name, entity.entity_type) not in entities:
                entities.append((entity.name, entity.entity_type))
    for relationship in RELATIONSHIPS:
        for name in relationship[:2]:
            if not any(item[0] == name for item in entities):
                entities.append((name, "Topic"))

    dim_entity = [
        {
            "entity_key": index + 1,
            "entity_name": name,
            "entity_type": entity_type,
        }
        for index, (name, entity_type) in enumerate(entities)
    ]

    dim_sentiment = [
        {"sentiment_key": 1, "sentiment_label": "Positive"},
        {"sentiment_key": 2, "sentiment_label": "Neutral"},
        {"sentiment_key": 3, "sentiment_label": "Negative"},
    ]

    return {
        "dim_date": dim_date,
        "dim_source": dim_source,
        "dim_event": dim_event,
        "dim_topic": dim_topic,
        "dim_entity": dim_entity,
        "dim_sentiment": dim_sentiment,
    }


def generate_raw_content(records: int, narrative_rows: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    weighted_rows = [(row, max(1, int(row["volume"]))) for row in narrative_rows]
    rows: list[dict[str, Any]] = []
    source_ids = [source["source_id"] for source in SOURCES]
    templates = [
        "{topic} is shifting public discussion around {event}.",
        "Analysts are watching {topic} as {event} gains attention.",
        "Public reaction to {topic} shows a new phase in {event}.",
        "The {topic} narrative continues to reshape the wider {event} story.",
        "Community discussion links {topic} with fast changing sentiment in {event}.",
    ]

    population = [item[0] for item in weighted_rows]
    weights = [item[1] for item in weighted_rows]
    for index in range(1, records + 1):
        row = rng.choices(population, weights=weights, k=1)[0]
        month = datetime.strptime(row["date"], "%Y-%m-%d").date()
        day_offset = rng.randint(0, 27)
        content_date = month + timedelta(days=day_offset)
        sentiment_score = float(row["sentiment_score"]) + rng.uniform(-0.18, 0.18)
        if sentiment_score > 0.12:
            sentiment_label = "Positive"
        elif sentiment_score < -0.12:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"

        engagement = int(max(1, float(row["narrative_strength"]) * rng.uniform(8, 34)))
        reach = int(engagement * rng.uniform(7, 42))
        rows.append(
            {
                "content_id": f"C{index:07d}",
                "date": content_date.isoformat(),
                "source_id": rng.choice(source_ids),
                "event_id": row["event_id"],
                "topic": row["topic"],
                "sentiment_label": sentiment_label,
                "sentiment_score": round(clamp(sentiment_score, -1, 1), 3),
                "engagement_score": engagement,
                "reach_score": reach,
                "popularity_score": round(clamp(engagement * 0.35 + reach * 0.015, 1, 1000), 2),
                "content": rng.choice(templates).format(topic=row["topic"], event=row["event_name"]),
            }
        )
    return rows


def build_fact_tables(
    raw_content: list[dict[str, Any]],
    narrative_rows: list[dict[str, Any]],
    sentiment_rows: list[dict[str, Any]],
    trend_rows: list[dict[str, Any]],
    entity_rows: list[dict[str, Any]],
    dimensions: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    source_key = {row["source_id"]: row["source_key"] for row in dimensions["dim_source"]}
    event_key = {row["event_id"]: row["event_key"] for row in dimensions["dim_event"]}
    topic_key = {row["topic_name"]: row["topic_key"] for row in dimensions["dim_topic"]}
    entity_key = {row["entity_name"]: row["entity_key"] for row in dimensions["dim_entity"]}
    sentiment_key = {row["sentiment_label"]: row["sentiment_key"] for row in dimensions["dim_sentiment"]}

    fact_content = [
        {
            "content_key": index + 1,
            "date_key": date_key(datetime.strptime(row["date"], "%Y-%m-%d").date()),
            "source_key": source_key[row["source_id"]],
            "event_key": event_key[row["event_id"]],
            "topic_key": topic_key[row["topic"]],
            "sentiment_key": sentiment_key[row["sentiment_label"]],
            "engagement_score": row["engagement_score"],
            "reach_score": row["reach_score"],
            "popularity_score": row["popularity_score"],
        }
        for index, row in enumerate(raw_content)
    ]

    fact_narrative = [
        {
            "narrative_fact_key": index + 1,
            "date_key": date_key(datetime.strptime(row["date"], "%Y-%m-%d").date()),
            "topic_key": topic_key[row["topic"]],
            "event_key": event_key[row["event_id"]],
            "narrative_strength": row["narrative_strength"],
            "growth_rate": row["growth_rate"],
            "influence_score": row["influence_score"],
            "lifecycle_stage": row["lifecycle_stage"],
        }
        for index, row in enumerate(narrative_rows)
    ]

    fact_sentiment: list[dict[str, Any]] = []
    sentiment_fact_key = 1
    for row in sentiment_rows:
        full_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
        totals = {
            "Positive": row["positive"],
            "Neutral": row["neutral"],
            "Negative": row["negative"],
        }
        for label, count in totals.items():
            fact_sentiment.append(
                {
                    "sentiment_fact_key": sentiment_fact_key,
                    "date_key": date_key(full_date),
                    "event_key": event_key[row["event_id"]],
                    "sentiment_key": sentiment_key[label],
                    "sentiment_score": row["sentiment_score"],
                    "polarity": 1 if label == "Positive" else -1 if label == "Negative" else 0,
                    "content_count": count,
                }
            )
            sentiment_fact_key += 1

    fact_trends = [
        {
            "trend_key": index + 1,
            "date_key": date_key(datetime.strptime(row["date"], "%Y-%m-%d").date()),
            "topic_key": topic_key[row["topic"]],
            "event_key": event_key[row["event_id"]],
            "trend_score": row["trend_score"],
            "growth_rate": row["growth_rate"],
            "momentum": row["momentum"],
        }
        for index, row in enumerate(trend_rows)
    ]

    fact_entity_mentions = [
        {
            "mention_key": index + 1,
            "entity_key": entity_key[row["entity_name"]],
            "event_key": event_key[row["event_id"]],
            "date_key": date_key(datetime.strptime(row["date"], "%Y-%m-%d").date()),
            "mention_count": row["mention_count"],
            "mention_strength": row["mention_strength"],
        }
        for index, row in enumerate(entity_rows)
    ]

    entity_relationships = []
    for index, (source, target, relation, strength) in enumerate(RELATIONSHIPS, start=1):
        entity_relationships.append(
            {
                "relationship_key": index,
                "source_entity_key": entity_key[source],
                "target_entity_key": entity_key[target],
                "relationship_type": relation,
                "strength_score": strength,
            }
        )

    return {
        "fact_content": fact_content,
        "fact_narrative": fact_narrative,
        "fact_sentiment": fact_sentiment,
        "fact_trends": fact_trends,
        "fact_entity_mentions": fact_entity_mentions,
        "entity_relationships": entity_relationships,
    }


def aggregate_mart(
    narrative_rows: list[dict[str, Any]],
    sentiment_rows: list[dict[str, Any]],
    trend_rows: list[dict[str, Any]],
    entity_rows: list[dict[str, Any]],
    raw_content: list[dict[str, Any]],
    dimensions: dict[str, list[dict[str, Any]]],
    facts: dict[str, list[dict[str, Any]]],
    quality_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    latest_date = max(row["date"] for row in narrative_rows)
    latest_narratives = [row for row in narrative_rows if row["date"] == latest_date]

    sentiment_totals = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for row in sentiment_rows:
        if row["date"] == latest_date:
            sentiment_totals["Positive"] += int(row["positive"])
            sentiment_totals["Neutral"] += int(row["neutral"])
            sentiment_totals["Negative"] += int(row["negative"])

    event_latest: dict[str, dict[str, Any]] = {}
    for event in EVENTS:
        rows = [row for row in latest_narratives if row["event_id"] == event.event_id]
        sentiment_event_rows = [row for row in sentiment_rows if row["event_id"] == event.event_id and row["date"] == latest_date]
        event_sentiment = sum(float(row["sentiment_score"]) for row in sentiment_event_rows) / max(1, len(sentiment_event_rows))
        strength = sum(float(row["narrative_strength"]) for row in rows) / max(1, len(rows))
        growth = sum(float(row["growth_rate"]) for row in rows) / max(1, len(rows))
        influence = sum(float(row["influence_score"]) for row in rows) / max(1, len(rows))
        stage = max(rows, key=lambda item: float(item["narrative_strength"]))["lifecycle_stage"] if rows else "Emerging"
        event_latest[event.event_id] = {
            "id": event.event_id,
            "name": event.name,
            "category": event.category,
            "region": event.region,
            "narrativeStrength": round(strength, 2),
            "growthRate": round(growth, 2),
            "influenceScore": round(influence, 2),
            "sentimentScore": round(event_sentiment, 3),
            "sentimentLabel": "Positive" if event_sentiment > 0.12 else "Negative" if event_sentiment < -0.12 else "Neutral",
            "lifecycleStage": stage,
        }

    narratives: list[dict[str, Any]] = []
    grouped_narratives: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in narrative_rows:
        grouped_narratives[(row["event_id"], row["topic"])].append(row)

    for (event_id, topic), rows in grouped_narratives.items():
        rows = sorted(rows, key=lambda item: item["date"])
        latest = rows[-1]
        related = [
            item["topic"]
            for item in latest_narratives
            if item["event_id"] == event_id and item["topic"] != topic
        ][:4]
        narratives.append(
            {
                "id": f"{event_id}-{topic.lower().replace(' ', '-')}",
                "eventId": event_id,
                "eventName": latest["event_name"],
                "topic": topic,
                "category": latest["topic_category"],
                "latestStrength": latest["narrative_strength"],
                "growthRate": latest["growth_rate"],
                "influenceScore": latest["influence_score"],
                "sentimentScore": latest["sentiment_score"],
                "lifecycleStage": latest["lifecycle_stage"],
                "relatedNarratives": related,
                "timeline": [
                    {
                        "date": row["date"],
                        "month": row["date"][:7],
                        "strength": row["narrative_strength"],
                        "growth": row["growth_rate"],
                        "influence": row["influence_score"],
                        "sentiment": row["sentiment_score"],
                        "volume": row["volume"],
                        "stage": row["lifecycle_stage"],
                    }
                    for row in rows
                ],
            }
        )

    narratives.sort(key=lambda item: (float(item["latestStrength"]), float(item["influenceScore"])), reverse=True)

    top_growing = sorted(
        [
            {
                "topic": row["topic"],
                "eventName": row["event_name"],
                "trendScore": row["narrative_strength"],
                "growthRate": row["growth_rate"],
                "momentum": next((trend["momentum"] for trend in trend_rows if trend["date"] == latest_date and trend["topic"] == row["topic"] and trend["event_id"] == row["event_id"]), 0),
            }
            for row in latest_narratives
        ],
        key=lambda item: float(item["growthRate"]),
        reverse=True,
    )[:8]

    entity_group: dict[str, dict[str, Any]] = {}
    for row in entity_rows:
        entity = entity_group.setdefault(
            row["entity_name"],
            {
                "name": row["entity_name"],
                "type": row["entity_type"],
                "totalMentions": 0,
                "latestMentions": 0,
                "mentionStrength": 0.0,
                "eventName": row["event_name"],
                "timeline": [],
            },
        )
        entity["totalMentions"] += int(row["mention_count"])
        if row["date"] == latest_date:
            entity["latestMentions"] += int(row["mention_count"])
            entity["mentionStrength"] = max(float(entity["mentionStrength"]), float(row["mention_strength"]))
        entity["timeline"].append({"date": row["date"], "mentions": row["mention_count"], "strength": row["mention_strength"]})

    entities = sorted(entity_group.values(), key=lambda item: (item["latestMentions"], item["mentionStrength"]), reverse=True)

    sentiment_timeline: dict[str, dict[str, int]] = defaultdict(lambda: {"date": "", "positive": 0, "neutral": 0, "negative": 0})
    for row in sentiment_rows:
        bucket = sentiment_timeline[row["date"]]
        bucket["date"] = row["date"][:7]
        bucket["positive"] += int(row["positive"])
        bucket["neutral"] += int(row["neutral"])
        bucket["negative"] += int(row["negative"])

    graph_nodes: dict[str, dict[str, Any]] = {}
    for entity in entities[:16]:
        graph_nodes[entity["name"]] = {
            "id": entity["name"],
            "label": entity["name"],
            "type": entity["type"],
            "score": round(float(entity["mentionStrength"]), 2),
        }
    for narrative in narratives[:8]:
        graph_nodes[narrative["topic"]] = {
            "id": narrative["topic"],
            "label": narrative["topic"],
            "type": "Narrative",
            "score": narrative["latestStrength"],
        }

    graph_links = [
        {
            "source": source,
            "target": target,
            "type": relation,
            "strength": strength,
        }
        for source, target, relation, strength in RELATIONSHIPS
        if source in graph_nodes and target in graph_nodes
    ]

    predictions = []
    for narrative in narratives[:6]:
        timeline = narrative["timeline"][-6:]
        last_strength = float(timeline[-1]["strength"])
        avg_growth = sum(float(item["growth"]) for item in timeline[-4:]) / 4
        forecast_points = []
        forecast_strength = last_strength
        for step in range(1, 5):
            forecast_strength = clamp(forecast_strength * (1 + avg_growth / 100 * 0.28), 1, 100)
            forecast_points.append(
                {
                    "period": f"+{step}m",
                    "strength": round(forecast_strength, 2),
                    "confidence": round(clamp(92 - step * 7 - abs(avg_growth) * 0.08, 55, 91), 2),
                }
            )
        predictions.append(
            {
                "narrative": narrative["topic"],
                "eventName": narrative["eventName"],
                "expectedGrowth": round(avg_growth * 0.72, 2),
                "direction": "Growing" if avg_growth > 5 else "Declining" if avg_growth < -5 else "Stable",
                "forecast": forecast_points,
            }
        )

    replay_frames = []
    ai_rows = [row for row in narrative_rows if row["event_id"] == "ai-revolution"]
    for month in sorted({row["date"] for row in ai_rows}):
        month_rows = [row for row in ai_rows if row["date"] == month]
        if not month_rows:
            continue
        top = sorted(month_rows, key=lambda item: float(item["narrative_strength"]), reverse=True)[:4]
        replay_frames.append(
            {
                "date": month,
                "label": month[:7],
                "dominantNarrative": top[0]["topic"],
                "stage": top[0]["lifecycle_stage"],
                "strength": top[0]["narrative_strength"],
                "sentiment": top[0]["sentiment_score"],
                "activeNarratives": [
                    {
                        "topic": row["topic"],
                        "strength": row["narrative_strength"],
                        "stage": row["lifecycle_stage"],
                    }
                    for row in top
                ],
            }
        )

    total_quality = sum(float(row["quality_score"]) for row in quality_rows) / max(1, len(quality_rows))
    total_content = len(raw_content)
    health_score = round(
        clamp(
            sum(float(item["narrativeStrength"]) + float(item["influenceScore"]) for item in event_latest.values())
            / max(1, len(event_latest) * 2),
            1,
            100,
        ),
        2,
    )

    intelligence_feed = [
        {
            "title": f"{top_growing[0]['topic']} is accelerating",
            "body": f"{top_growing[0]['eventName']} shows {top_growing[0]['growthRate']}% month-over-month growth in the latest warehouse snapshot.",
            "severity": "High",
        },
        {
            "title": f"{entities[0]['name']} leads entity influence",
            "body": f"{entities[0]['name']} recorded {entities[0]['latestMentions']:,} latest-period mentions with a strength score of {entities[0]['mentionStrength']}.",
            "severity": "Medium",
        },
        {
            "title": "Data quality gate passed",
            "body": f"ETL profiling reports an overall quality score of {total_quality:.1f}% across generated warehouse outputs.",
            "severity": "Low",
        },
    ]

    source_counts = defaultdict(int)
    source_id_to_name = {row["source_id"]: row["source_name"] for row in dimensions["dim_source"]}
    for row in raw_content:
        name = source_id_to_name.get(row["source_id"], row["source_id"])
        source_counts[name] += 1

    return {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "historicalThrough": latest_date,
        "overview": {
            "totalRecords": total_content,
            "activeEvents": len(EVENTS),
            "activeNarratives": len(narratives),
            "narrativeHealthScore": health_score,
            "warehouseQualityScore": round(total_quality, 2),
            "sentimentDistribution": [
                {"label": label, "value": value}
                for label, value in sentiment_totals.items()
            ],
        },
        "warehouseStats": {
            "dimensions": {name: len(rows) for name, rows in dimensions.items()},
            "facts": {name: len(rows) for name, rows in facts.items()},
            "source_mix": dict(source_counts),
        },
        "events": list(event_latest.values()),
        "narratives": narratives,
        "topGrowingTopics": top_growing,
        "entities": entities[:18],
        "sentimentTimeline": [sentiment_timeline[key] for key in sorted(sentiment_timeline)],
        "predictions": predictions,
        "graph": {
            "nodes": list(graph_nodes.values()),
            "links": graph_links,
        },
        "replayFrames": replay_frames,
        "dataQuality": quality_rows,
        "intelligenceFeed": intelligence_feed,
        "reportSummary": {
            "title": "NarrativeIQ Intelligence Summary",
            "eventFocus": "Artificial Intelligence Revolution",
            "period": f"2023-01 to {latest_date[:7]}",
            "primaryFinding": intelligence_feed[0]["body"],
            "recommendedDemoFlow": [
                "Open overview dashboard",
                "Replay AI narrative evolution",
                "Expand the knowledge graph",
                "Show prediction center",
                "Export intelligence summary",
            ],
        },
    }


def build_quality_rows(raw_content: list[dict[str, Any]], dimensions: dict[str, list[dict[str, Any]]], facts: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    datasets = {"raw_content": raw_content, **dimensions, **facts}
    rows = []
    for name, records in datasets.items():
        record_count = len(records)
        missing = 0
        field_count = 0
        seen = set()
        duplicates = 0
        for record in records:
            signature = tuple(sorted(record.items()))
            if signature in seen:
                duplicates += 1
            seen.add(signature)
            for value in record.values():
                field_count += 1
                if value in ("", None):
                    missing += 1
        completeness = 100 if field_count == 0 else round(100 - (missing / field_count * 100), 2)
        uniqueness = 100 if record_count == 0 else round(100 - (duplicates / record_count * 100), 2)
        consistency = 98.5 if record_count else 0
        timeliness = 97.8 if record_count else 0
        quality = round((completeness + uniqueness + consistency + timeliness) / 4, 2)
        rows.append(
            {
                "dataset": name,
                "record_count": record_count,
                "completeness": completeness,
                "uniqueness": uniqueness,
                "consistency": consistency,
                "timeliness": timeliness,
                "quality_score": quality,
            }
        )
    return rows


def _name_to_slug(name: str) -> str:
    """Convert a human dataset name to a filesystem-safe slug.

    Examples
    --------
    'NarrativeIQ Warehouse' -> 'narrativeiq_mart'
    'Tech Trends 2024'      -> 'tech_trends_2024_mart'
    """
    import re as _re
    slug = name.lower().strip()
    slug = _re.sub(r"[^a-z0-9]+", "_", slug)
    slug = slug.strip("_")
    # Always suffix with _mart so the backend scanner can identify these files.
    if not slug.endswith("_mart"):
        slug = slug + "_mart"
    return slug


def write_outputs(
    raw_content: list[dict[str, Any]],
    narrative_rows: list[dict[str, Any]],
    sentiment_rows: list[dict[str, Any]],
    trend_rows: list[dict[str, Any]],
    entity_rows: list[dict[str, Any]],
    dimensions: dict[str, list[dict[str, Any]]],
    facts: dict[str, list[dict[str, Any]]],
    quality_rows: list[dict[str, Any]],
    mart: dict[str, Any],
    dataset_name: str = "NarrativeIQ Warehouse",
) -> None:
    write_csv(RAW_DIR / "raw_content.csv", raw_content, list(raw_content[0].keys()))
    write_csv(DATASETS / "event_master.csv", [
        {
            "event_id": event.event_id,
            "event_name": event.name,
            "category": event.category,
            "region": event.region,
            "start_date": event.start_date,
            "end_date": event.end_date,
        }
        for event in EVENTS
    ], ["event_id", "event_name", "category", "region", "start_date", "end_date"])
    write_csv(DATASETS / "narrative_history.csv", narrative_rows, list(narrative_rows[0].keys()))
    write_csv(DATASETS / "sentiment_history.csv", sentiment_rows, list(sentiment_rows[0].keys()))
    write_csv(DATASETS / "topic_trends.csv", trend_rows, list(trend_rows[0].keys()))
    write_csv(DATASETS / "entity_mentions.csv", entity_rows, list(entity_rows[0].keys()))

    for name, rows in dimensions.items():
        write_csv(WAREHOUSE_DIR / f"{name}.csv", rows, list(rows[0].keys()))
    for name, rows in facts.items():
        write_csv(WAREHOUSE_DIR / f"{name}.csv", rows, list(rows[0].keys()))

    write_csv(WAREHOUSE_DIR / "data_quality_report.csv", quality_rows, list(quality_rows[0].keys()))

    # ── Named mart file ──────────────────────────────────────────────────────
    slug = _name_to_slug(dataset_name)
    mart_filename = f"{slug}.json"

    # Always keep the canonical default file as a symlink/copy so the API
    # fallback path (narrativeiq_mart.json) still works when no slug is given.
    default_filename = "narrativeiq_mart.json"

    MART_DIR.mkdir(parents=True, exist_ok=True)
    for filename in {mart_filename, default_filename}:
        with (MART_DIR / filename).open("w", encoding="utf-8") as handle:
            json.dump(mart, handle, indent=2)

    FRONTEND_PUBLIC_DATA.mkdir(parents=True, exist_ok=True)
    for filename in {mart_filename, default_filename}:
        with (FRONTEND_PUBLIC_DATA / filename).open("w", encoding="utf-8") as handle:
            json.dump(mart, handle, indent=2)


def run(records: int, seed: int, import_dir: str | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    for directory in [RAW_DIR, WAREHOUSE_DIR, MART_DIR, FRONTEND_DATA, FRONTEND_PUBLIC_DATA]:
        directory.mkdir(parents=True, exist_ok=True)

    imported_rows = []
    imported_sources = []
    
    resolved_import_dir = Path(import_dir) if import_dir else DATASETS / "imports"
    enriched_dir = DATASETS / "enriched"

    if resolved_import_dir.exists():
        for file_path in resolved_import_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                import_id = data.get("importId")
                if not import_id:
                    continue
                
                enriched_path = enriched_dir / f"{import_id}.json"
                if enriched_path.exists():
                    try:
                        data = json.loads(enriched_path.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                
                source_type = data.get("sourceType") or "manual"
                pack_name = data.get("name") or "Import Pack"
                
                source_id = import_id
                source_name = f"Import: {pack_name}"
                source_detail = {
                    "source_id": source_id,
                    "source_name": source_name,
                    "source_type": source_type.capitalize(),
                    "platform": "Import",
                }
                if source_detail not in imported_sources:
                    imported_sources.append(source_detail)
                
                rows = data.get("rows") or []
                for row in rows:
                    title = row.get("title") or row.get("value") or row.get("raw") or "Imported Item"
                    topic = row.get("topic") or "AI Assistants"
                    sentiment_label = row.get("sentiment") or row.get("sentiment_label") or "Neutral"
                    
                    engagement = row.get("engagement_score") or rng.randint(10, 80)
                    reach = row.get("reach_score") or engagement * rng.randint(10, 30)
                    popularity = row.get("popularity_score") or round(engagement * 0.35 + reach * 0.015, 2)
                    
                    content_date = row.get("date") or row.get("publishedAt") or row.get("importedAt") or "2026-06-01"
                    if "T" in content_date:
                        content_date = content_date.split("T")[0]
                    
                    imported_rows.append({
                        "date": content_date,
                        "source_id": source_id,
                        "event_id": row.get("event_id") or "ai-revolution",
                        "topic": topic,
                        "sentiment_label": sentiment_label,
                        "sentiment_score": row.get("sentiment_score") or 0.0,
                        "engagement_score": engagement,
                        "reach_score": reach,
                        "popularity_score": popularity,
                        "content": title,
                    })
            except Exception as e:
                print(f"Error loading import pack {file_path}: {e}")

    months = month_range(date(2023, 1, 1), date(2026, 6, 1))
    narrative_rows, sentiment_rows, trend_rows, entity_rows = generate_narrative_rows(months, rng)
    raw_content = generate_raw_content(records, narrative_rows, rng)
    
    for idx, row in enumerate(imported_rows):
        start_idx = len(raw_content) + idx + 1
        row["content_id"] = f"C{start_idx:07d}"
    raw_content.extend(imported_rows)
    
    dimensions = build_dimensions(months, imported_sources)
    facts = build_fact_tables(raw_content, narrative_rows, sentiment_rows, trend_rows, entity_rows, dimensions)
    quality_rows = build_quality_rows(raw_content, dimensions, facts)
    mart = aggregate_mart(narrative_rows, sentiment_rows, trend_rows, entity_rows, raw_content, dimensions, facts, quality_rows)

    # Inject dataset identity fields so the frontend can identify which mart
    # is loaded and show a human-readable name in the dataset switcher.
    dataset_name_val = getattr(run, "_dataset_name", "NarrativeIQ Warehouse")
    mart["datasetName"] = dataset_name_val
    mart["datasetSlug"] = _name_to_slug(dataset_name_val)

    write_outputs(raw_content, narrative_rows, sentiment_rows, trend_rows, entity_rows, dimensions, facts, quality_rows, mart, dataset_name=dataset_name_val)
    return mart


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate NarrativeIQ exhibition datasets and marts.")
    parser.add_argument("--records", type=int, default=50_000, help="Number of raw content records to generate.")
    parser.add_argument("--seed", type=int, default=130, help="Deterministic random seed.")
    parser.add_argument("--import-dir", type=str, default=None, help="Directory containing imported source packs.")
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="NarrativeIQ Warehouse",
        help="Human-readable dataset name. Determines the mart filename (e.g. 'Tech 2024' -> tech_2024_mart.json).",
    )
    args = parser.parse_args()

    # Attach dataset name to the run function so it can be picked up inside.
    run._dataset_name = args.dataset_name  # type: ignore[attr-defined]
    mart = run(records=args.records, seed=args.seed, import_dir=args.import_dir)
    slug = _name_to_slug(args.dataset_name)
    print("NarrativeIQ ETL complete")
    print(f"- dataset name: {args.dataset_name}")
    print(f"- dataset slug: {slug}")
    print(f"- raw records: {mart['overview']['totalRecords']:,}")
    print(f"- active narratives: {mart['overview']['activeNarratives']}")
    print(f"- warehouse quality: {mart['overview']['warehouseQualityScore']}%")
    print(f"- mart: {MART_DIR / f'{slug}.json'}")


if __name__ == "__main__":
    main()
