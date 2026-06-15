"""NarrativeIQ DeepSeek Enrichment Module.

Sprint 3 enrichment: topic classification, entity extraction,
sentiment analysis, and narrative summarization via DeepSeek.

Usage:
    from etl.deepseek_enrichment import enrich_rows
    enriched = enrich_rows(rows, api_key, model="deepseek-chat")
"""
from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"
BATCH_SIZE = 10  # max rows per API call
RETRY_DELAY = 2.0

SYSTEM_PROMPT = (
    "You are NarrativeIQ, a narrative intelligence enrichment engine. "
    "Analyze the provided source text and return a JSON object with exactly these fields: "
    '"topic" (string, the primary topic category), '
    '"entities" (array of up to 5 named entities as strings), '
    '"sentiment" (one of: Positive, Neutral, Negative), '
    '"summary" (one clear sentence describing the content, max 120 characters). '
    "Return only valid JSON, no markdown or extra text."
)


def _build_user_prompt(row: dict[str, Any]) -> str:
    title = str(row.get("title") or row.get("value") or row.get("raw") or "").strip()
    source = str(row.get("source") or "").strip()
    url = str(row.get("url") or "").strip()
    parts = [f"Title: {title}"]
    if source:
        parts.append(f"Source: {source}")
    if url:
        parts.append(f"URL: {url}")
    return "\n".join(parts)


def _call_deepseek(messages: list[dict], api_key: str, model: str, timeout: int = 20) -> str | None:
    body = json.dumps({
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "max_tokens": 256,
        "temperature": 0.2,
    }, ensure_ascii=False).encode("utf-8")
    request = Request(
        DEEPSEEK_API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "NarrativeIQ/0.1 enrichment",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload["choices"][0]["message"]["content"]
    except (URLError, KeyError, json.JSONDecodeError, IndexError):
        return None


def _safe_parse(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _enrich_single(row: dict[str, Any], api_key: str, model: str) -> dict[str, Any]:
    """Enrich a single row with DeepSeek intelligence."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(row)},
    ]
    raw = _call_deepseek(messages, api_key, model)
    enrichment = _safe_parse(raw)

    # Normalise enrichment fields with safe defaults
    topic = str(enrichment.get("topic") or "General").strip()[:120]
    entities = enrichment.get("entities")
    if not isinstance(entities, list):
        entities = []
    entities = [str(entity).strip() for entity in entities[:5] if entity]
    sentiment_raw = str(enrichment.get("sentiment") or "").strip()
    sentiment = sentiment_raw if sentiment_raw in {"Positive", "Neutral", "Negative"} else "Neutral"
    summary = str(enrichment.get("summary") or "").strip()[:160]

    return {
        **row,
        "enriched": True,
        "topic": topic,
        "entities": entities,
        "sentiment": sentiment,
        "summary": summary,
        "enrichedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def enrich_rows(
    rows: list[dict[str, Any]],
    api_key: str,
    model: str = DEFAULT_MODEL,
    batch_size: int = BATCH_SIZE,
    on_progress: Any = None,
) -> list[dict[str, Any]]:
    """Enrich a list of source rows with DeepSeek intelligence.

    Args:
        rows: List of source row dicts (each must have at least a 'title' or 'raw' key).
        api_key: DeepSeek API key.
        model: DeepSeek model name (default: deepseek-chat).
        batch_size: Max rows to process in sequence before pausing.
        on_progress: Optional callable(enriched_count, total) for progress updates.

    Returns:
        List of row dicts with enrichment fields added.
    """
    if not api_key:
        raise ValueError("DeepSeek API key is required for enrichment.")
    if not rows:
        return []

    enriched: list[dict[str, Any]] = []
    total = len(rows)

    for index, row in enumerate(rows):
        result = _enrich_single(row, api_key, model)
        enriched.append(result)
        if on_progress:
            on_progress(index + 1, total)
        # Small pause between calls to respect rate limits
        if (index + 1) % batch_size == 0 and (index + 1) < total:
            time.sleep(RETRY_DELAY)

    return enriched


def enrich_import_artifact(
    artifact: dict[str, Any],
    api_key: str,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Enrich all rows in an import artifact dict and return the enriched artifact."""
    rows = artifact.get("rows") or []
    enriched_rows = enrich_rows(rows, api_key=api_key, model=model)
    return {
        **artifact,
        "rows": enriched_rows,
        "enrichedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "enrichedModel": model,
        "enrichedCount": len(enriched_rows),
    }


if __name__ == "__main__":
    # Quick CLI test: python -m etl.deepseek_enrichment
    import sys
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        print("Set DEEPSEEK_API_KEY to test enrichment.", file=sys.stderr)
        sys.exit(1)
    sample = [
        {"title": "OpenAI releases new reasoning model", "source": "TechCrunch", "url": "https://example.com"},
        {"title": "Pakistan cricket team wins series against India", "source": "Dawn", "url": "https://dawn.com"},
    ]
    results = enrich_rows(sample, api_key=key)
    print(json.dumps(results, indent=2, ensure_ascii=False))
