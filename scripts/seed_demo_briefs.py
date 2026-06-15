from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


DEFAULT_TOPICS = [
    "OpenAI",
    "K-pop",
    "WWE",
    "Pakistan Elections",
    "Climate Risk",
]


def request_json(url: str, method: str = "GET", payload: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"

    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed NarrativeIQ demo live-topic snapshots through the FastAPI API.")
    parser.add_argument("--api", default="http://127.0.0.1:8000", help="FastAPI base URL.")
    parser.add_argument("--topics", nargs="*", default=DEFAULT_TOPICS, help="Topics to generate and save.")
    parser.add_argument("--force", action="store_true", help="Save a fresh snapshot even if the topic already exists.")
    args = parser.parse_args()

    api = args.api.rstrip("/")
    try:
        status = request_json(f"{api}/admin/status", timeout=10)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"Seed skipped: FastAPI is not reachable ({exc}).")
        return 1

    if not status.get("postgresConfigured"):
        print("Seed skipped: PostgreSQL is not configured.")
        return 0

    saved = request_json(f"{api}/topic-intelligence/saved?limit=25", timeout=10)
    existing = {str(item.get("topicName", "")).lower() for item in saved.get("snapshots", [])}

    completed = 0
    skipped = 0
    failed = 0

    for topic in args.topics:
        normalized = topic.lower()
        if normalized in existing and not args.force:
            print(f"Skip: {topic} already has a saved snapshot.")
            skipped += 1
            continue

        try:
            print(f"Generate: {topic}")
            brief = request_json(f"{api}/topic-intelligence?q={quote(topic)}", timeout=25)
            result = request_json(f"{api}/topic-intelligence/save", method="POST", payload=brief, timeout=25)
            print(
                "Saved: "
                f"{topic} -> snapshot {result.get('snapshotKey')} "
                f"({result.get('sourcesSaved')} source rows)"
            )
            completed += 1
            time.sleep(0.4)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"Failed: {topic} ({exc})")
            failed += 1

    print(
        json.dumps(
            {
                "status": "completed" if failed == 0 else "partial",
                "saved": completed,
                "skipped": skipped,
                "failed": failed,
            }
        )
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
