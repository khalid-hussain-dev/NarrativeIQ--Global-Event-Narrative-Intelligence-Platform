from datetime import datetime
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[3]
IMPORT_DIR = PROJECT_ROOT / "datasets" / "imports"

def get_helpers():
    from app.main import (
        write_audit_log,
        audit_timestamp,
    )
    return write_audit_log, audit_timestamp


def parse_import_rows(raw_content: str) -> list[dict[str, Any]]:
    content = raw_content.strip()
    if not content:
        return []

    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return [row if isinstance(row, dict) else {"value": row} for row in parsed[:100]]
        if isinstance(parsed, dict):
            rows = parsed.get("rows") or parsed.get("items") or parsed.get("records")
            if isinstance(rows, list):
                return [row if isinstance(row, dict) else {"value": row} for row in rows[:100]]
            return [parsed]
    except json.JSONDecodeError:
        pass

    rows = []
    for line in content.splitlines()[:100]:
        cleaned = line.strip()
        if not cleaned:
            continue
        parts = [part.strip() for part in cleaned.split(",")]
        rows.append(
            {
                "title": parts[0],
                "source": parts[1] if len(parts) > 1 else "manual",
                "url": parts[2] if len(parts) > 2 else None,
                "raw": cleaned,
            }
        )
    return rows


def import_source_pack(payload: dict[str, Any]) -> dict[str, Any]:
    write_audit_log, audit_timestamp = get_helpers()
    name = str(payload.get("name") or "Manual Source Pack").strip()[:120]
    source_type = str(payload.get("sourceType") or "manual").strip()[:80]
    notes = str(payload.get("notes") or "").strip()[:500]
    content = str(payload.get("content") or "").strip()
    rows = parse_import_rows(content)
    if not rows:
        raise ValueError("Import content did not contain any rows.")

    import_id = f"import_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"
    artifact = {
        "importId": import_id,
        "name": name,
        "sourceType": source_type,
        "notes": notes,
        "importedAt": audit_timestamp(),
        "rowCount": len(rows),
        "rows": rows,
    }
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = IMPORT_DIR / f"{import_id}.json"
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = write_audit_log(
        "source_pack_import",
        "completed",
        f"Imported source pack {name} with {len(rows)} row{'s' if len(rows) != 1 else ''}.",
        {
            "importId": import_id,
            "name": name,
            "sourceType": source_type,
            "rowCount": len(rows),
            "artifactPath": str(artifact_path),
        },
    )
    return {
        "status": "imported",
        "importId": import_id,
        "name": name,
        "sourceType": source_type,
        "rowCount": len(rows),
        "artifactPath": str(artifact_path),
        "auditId": audit["id"],
    }
