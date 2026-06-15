from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MARTS_DIR = PROJECT_ROOT / "datasets" / "marts"
DEFAULT_MART = MARTS_DIR / "narrativeiq_mart.json"
WAREHOUSE_DIR = PROJECT_ROOT / "datasets" / "warehouse"

# -- TTL-based cache -----------------------------------------------------------
# We replace @lru_cache with a time-to-live cache so the mart is re-read from
# disk at most every MART_CACHE_TTL seconds.  This means that immediately after
# an Admin "Run ETL" overwrites narrativeiq_mart.json, the next dashboard
# request (within <=30 s) will serve fresh data without any server restart.

MART_CACHE_TTL: int = 30  # seconds

_mart_cache: dict[str, Any] | None = None
_mart_cache_time: float = 0.0

# Per-slug caches for the dataset switcher
_slug_cache: dict[str, dict[str, Any]] = {}
_slug_cache_times: dict[str, float] = {}


def _slug_to_label(slug: str) -> str:
    """Convert a slug like 'tech_trends_mart' to 'Tech Trends Mart'."""
    return slug.replace("_", " ").title()


def load_mart() -> dict[str, Any]:
    global _mart_cache, _mart_cache_time
    now = time.monotonic()
    if _mart_cache is not None and (now - _mart_cache_time) < MART_CACHE_TTL:
        return _mart_cache

    configured = os.getenv("NARRATIVEIQ_MART_PATH")
    mart_path = Path(configured) if configured else DEFAULT_MART
    if not mart_path.exists():
        # Return stale cache rather than crashing if file was temporarily missing.
        if _mart_cache is not None:
            return _mart_cache
        raise FileNotFoundError(
            f"NarrativeIQ mart not found at {mart_path}. "
            "Run `python etl/pipeline.py --records 50000` first."
        )
    with mart_path.open("r", encoding="utf-8") as fh:
        _mart_cache = json.load(fh)
    _mart_cache_time = now
    return _mart_cache


def clear_mart_cache() -> None:
    """Force the next load_mart() call to re-read from disk immediately."""
    global _mart_cache_time
    _mart_cache_time = 0.0


def load_mart_by_slug(slug: str) -> dict[str, Any]:
    """Load a specific mart by its slug, with TTL caching."""
    now = time.monotonic()
    cached = _slug_cache.get(slug)
    cached_at = _slug_cache_times.get(slug, 0.0)
    if cached is not None and (now - cached_at) < MART_CACHE_TTL:
        return cached

    mart_path = MARTS_DIR / f"{slug}.json"
    if not mart_path.exists():
        raise FileNotFoundError(
            f"Mart '{slug}' not found at {mart_path}. "
            "Run ETL with --dataset-name matching this slug, or pick a different dataset."
        )
    with mart_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    _slug_cache[slug] = data
    _slug_cache_times[slug] = now
    return data


def list_marts() -> list[dict[str, Any]]:
    """Scan the marts directory and return metadata for each mart JSON file.

    Each entry contains:
        slug          - filesystem slug (stem of the file, e.g. 'tech_trends_mart')
        name          - human-readable name (from mart JSON 'datasetName' field, or slug)
        filename      - actual filename
        generatedAt   - ISO timestamp from mart JSON
        totalRecords  - record count from mart JSON overview
        sizeBytes     - file size in bytes
    """
    if not MARTS_DIR.exists():
        return []

    results: list[dict[str, Any]] = []
    for path in sorted(MARTS_DIR.glob("*_mart.json")):
        slug = path.stem
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            results.append({
                "slug": slug,
                "name": data.get("datasetName") or _slug_to_label(slug),
                "filename": path.name,
                "generatedAt": data.get("generatedAt", ""),
                "totalRecords": data.get("overview", {}).get("totalRecords", 0),
                "sizeBytes": path.stat().st_size,
            })
        except Exception:
            # Corrupt file - skip silently
            pass
    return results


def warehouse_file_stats() -> dict[str, Any]:
    if not WAREHOUSE_DIR.exists():
        return {"exists": False, "files": [], "totalBytes": 0}
    files = [
        {"name": path.name, "bytes": path.stat().st_size}
        for path in sorted(WAREHOUSE_DIR.glob("*.csv"))
    ]
    return {
        "exists": True,
        "files": files,
        "totalBytes": sum(item["bytes"] for item in files),
    }
