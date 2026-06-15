from __future__ import annotations

from app.services.mart_service import load_mart, clear_mart_cache, warehouse_file_stats, list_marts, load_mart_by_slug
from app.services.admin_service import parse_import_rows, import_source_pack
from app.services.topic_service import (
    tokenize,
    text_score,
    clamp,
    fetch_json,
    month_back,
    sentiment_from_text,
    wikipedia_topic,
    gdelt_articles,
    google_news_articles,
    live_news_articles,
    extract_live_entities,
    live_topic_profile,
    nearest_topic_profile,
    ensure_live_topic_schema,
    save_topic_brief,
    list_saved_topic_briefs,
    saved_topic_brief,
)

import json
import math
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4
from xml.etree import ElementTree
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from fastapi import Body, Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import asyncio
from contextlib import asynccontextmanager



PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MART = PROJECT_ROOT / "datasets" / "marts" / "narrativeiq_mart.json"
PIPELINE_SCRIPT = PROJECT_ROOT / "etl" / "pipeline.py"
WAREHOUSE_LOADER = PROJECT_ROOT / "etl" / "load_postgres.py"
WAREHOUSE_DIR = PROJECT_ROOT / "datasets" / "warehouse"
IMPORT_DIR = PROJECT_ROOT / "datasets" / "imports"
LIVE_TOPIC_SCHEMA = PROJECT_ROOT / "warehouse" / "003_live_topic_schema.sql"
REPORT_GENERATOR = PROJECT_ROOT / "reports" / "generate_report.py"
REPORT_PDF_EXPORTER = PROJECT_ROOT / "reports" / "export_report_pdf.py"
REPORT_HTML = PROJECT_ROOT / "reports" / "generated" / "narrativeiq_exhibition_report.html"
REPORT_PDF = PROJECT_ROOT / "reports" / "generated" / "narrativeiq_exhibition_report.pdf"
AUDIT_LOG = PROJECT_ROOT / "logs" / "admin_audit.jsonl"
ENRICHED_DIR = PROJECT_ROOT / "datasets" / "enriched"
SCHEDULE_CONFIG_FILE = PROJECT_ROOT / "logs" / "ingestion_schedule.json"


def load_project_env() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_project_env()


class IngestionSchedulerState:
    def __init__(self):
        self.interval_minutes = 0
        self.enabled = False
        self.last_run = None
        self.next_run = None
        self.refreshed_count = 0
        self.task = None

scheduler_state = IngestionSchedulerState()


def load_scheduler_config() -> dict[str, Any]:
    if SCHEDULE_CONFIG_FILE.exists():
        try:
            return json.loads(SCHEDULE_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"interval_minutes": 0, "enabled": False}


def save_scheduler_config(interval_minutes: int, enabled: bool) -> None:
    SCHEDULE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_CONFIG_FILE.write_text(
        json.dumps({"interval_minutes": interval_minutes, "enabled": enabled}, indent=2),
        encoding="utf-8"
    )


def get_all_saved_topic_names() -> list[str]:
    if not postgres_configured():
        return []
    try:
        sql = "SET search_path TO narrativeiq; SELECT DISTINCT topic_name FROM dim_live_topic;"
        output = run_database_sql(sql, extra_args=["-t", "-A"])
        return [line.strip() for line in output.splitlines() if line.strip()]
    except Exception:
        return []


async def run_ingestion_cycle():
    topic_names = get_all_saved_topic_names()
    if not topic_names:
        topic_names = ["Artificial Intelligence"]
    
    for topic in topic_names:
        try:
            loop = asyncio.get_event_loop()
            profile = await loop.run_in_executor(None, live_topic_profile, topic)
            if profile and postgres_configured():
                await loop.run_in_executor(None, save_topic_brief, profile)
                scheduler_state.refreshed_count += 1
        except Exception as e:
            write_audit_log(
                "scheduled_ingestion",
                "failed",
                f"Failed to auto-refresh topic {topic}: {str(e)[:200]}"
            )


async def scheduler_loop():
    await asyncio.sleep(5)
    while True:
        try:
            config = load_scheduler_config()
            interval = config.get("interval_minutes", 0)
            enabled = config.get("enabled", False)
            
            scheduler_state.interval_minutes = interval
            scheduler_state.enabled = enabled
            
            if not enabled or interval <= 0:
                scheduler_state.next_run = None
                await asyncio.sleep(10)
                continue
            
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            scheduler_state.next_run = (now + timedelta(minutes=interval)).isoformat() + "Z"
            
            sleep_time = interval * 60
            elapsed = 0
            while elapsed < sleep_time:
                await asyncio.sleep(10)
                elapsed += 10
                current_config = load_scheduler_config()
                if not current_config.get("enabled", False) or current_config.get("interval_minutes", 0) != interval:
                    break
            else:
                scheduler_state.last_run = datetime.utcnow().isoformat() + "Z"
                write_audit_log(
                    "scheduled_ingestion",
                    "started",
                    f"Started background scheduled live ingestion loop for {len(get_all_saved_topic_names())} topics."
                )
                await run_ingestion_cycle()
                write_audit_log(
                    "scheduled_ingestion",
                    "completed",
                    f"Background scheduled live ingestion loop completed. Refreshed count: {scheduler_state.refreshed_count}."
                )
        except asyncio.CancelledError:
            break
        except Exception as e:
            try:
                write_audit_log(
                    "scheduled_ingestion",
                    "failed",
                    f"Scheduler error in loop: {str(e)[:200]}"
                )
            except Exception:
                pass
            await asyncio.sleep(10)


def require_admin_key(x_admin_key: str = Header(default=None, alias="X-Admin-Key")) -> None:
    admin_key = os.getenv("NARRATIVEIQ_ADMIN_KEY")
    if not admin_key:
        return
    if x_admin_key != admin_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_scheduler_config()
    scheduler_state.interval_minutes = config.get("interval_minutes", 0)
    scheduler_state.enabled = config.get("enabled", False)
    scheduler_state.task = asyncio.create_task(scheduler_loop())
    yield
    if scheduler_state.task:
        scheduler_state.task.cancel()
        try:
            await scheduler_state.task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="NarrativeIQ API",
    description="Warehouse-backed APIs for narrative intelligence, entity analysis, sentiment, predictions, and graph exploration.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def command_result(command: list[str], timeout: int = 180) -> dict[str, Any]:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "command": command,
        "returnCode": completed.returncode,
        "durationSeconds": round(time.perf_counter() - started, 2),
        "stdout": completed.stdout[-6000:],
        "stderr": completed.stderr[-6000:],
    }


def database_url() -> str | None:
    return os.getenv("NARRATIVEIQ_DATABASE_URL") or os.getenv("DATABASE_URL")


def postgres_configured() -> bool:
    return bool(database_url() or os.getenv("PGDATABASE"))


def run_database_sql(sql: str, extra_args: list[str] | None = None) -> str:
    import shutil

    url = database_url()
    psql = shutil.which("psql")
    if not psql and sys.platform == "win32":
        for ver in ["17", "16", "15", "14", "13", "12"]:
            candidate = f"C:\\Program Files\\PostgreSQL\\{ver}\\bin\\psql.exe"
            if os.path.exists(candidate):
                psql = candidate
                break
    if not url:
        raise RuntimeError("PostgreSQL is not configured. Set NARRATIVEIQ_DATABASE_URL or DATABASE_URL.")
    if not psql:
        raise RuntimeError("psql was not found on PATH.")

    args = [psql, "-v", "ON_ERROR_STOP=1", "--dbname", url]
    if extra_args:
        args.extend(extra_args)
    env = os.environ.copy()
    env["PGCLIENTENCODING"] = "UTF8"

    completed = subprocess.run(
        args,
        cwd=PROJECT_ROOT,
        input=sql,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "Database command failed."
        raise RuntimeError(detail[-2000:])
    return completed.stdout.strip()


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def sql_json(value: Any) -> str:
    return sql_literal(json.dumps(value, ensure_ascii=False))



def audit_timestamp() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def write_audit_log(action: str, status: str, summary: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    entry = {
        "id": f"audit_{uuid4().hex[:12]}",
        "timestamp": audit_timestamp(),
        "action": action,
        "status": status,
        "summary": summary,
        "details": details or {},
    }
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return entry


def read_audit_log(limit: int = 12) -> dict[str, Any]:
    safe_limit = max(1, min(50, int(limit)))
    entries: list[dict[str, Any]] = []
    if AUDIT_LOG.exists():
        lines = AUDIT_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in reversed(lines):
            if len(entries) >= safe_limit:
                break
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return {"logPath": str(AUDIT_LOG), "entries": entries}


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "NarrativeIQ API",
        "status": "running",
        "message": "Use /health, /dashboard, /topic-intelligence?q=your-topic, or /docs.",
        "docs": "/docs",
        "frontend": "http://localhost:3000",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    mart = load_mart()
    return {
        "status": "ok",
        "generatedAt": mart["generatedAt"],
        "historicalThrough": mart["historicalThrough"],
        "records": mart["overview"]["totalRecords"],
        "postgresConfigured": postgres_configured(),
    }


@app.get("/dashboard")
def dashboard() -> dict[str, Any]:
    return load_mart()


@app.get("/datasets/marts")
def datasets_list() -> list[dict[str, Any]]:
    """List all named mart datasets available on disk."""
    return list_marts()


@app.get("/datasets/marts/{slug}")
def dataset_by_slug(slug: str) -> dict[str, Any]:
    """Load a specific mart dataset by its slug (e.g. 'tech_trends_mart')."""
    try:
        return load_mart_by_slug(slug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/admin/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_name: str = Query(default="", max_length=80),
    admin_key: None = Depends(require_admin_key),
) -> dict[str, Any]:
    """Upload a CSV file and convert it into a named NarrativeIQ mart.

    The CSV is processed by the smart csv_adapter which auto-detects column
    roles (entities, metrics, dates, sentiment) and produces a full mart JSON.
    The mart is saved to datasets/marts/<slug>_mart.json and also copied to
    the frontend public/data directory so the static fallback works too.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    # Derive dataset name from filename if not provided
    stem = Path(file.filename).stem
    name = dataset_name.strip() if dataset_name.strip() else stem.replace("_", " ").title()

    # Write the upload to a temp file then run the adapter
    import tempfile
    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # Import adapter (lives in etl/csv_adapter.py, two levels up from here)
        import importlib.util
        adapter_path = PROJECT_ROOT / "etl" / "csv_adapter.py"
        spec = importlib.util.spec_from_file_location("csv_adapter", adapter_path)
        csv_adapter = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(csv_adapter)  # type: ignore[union-attr]

        mart = csv_adapter.csv_to_mart(tmp_path, dataset_name=name)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"CSV processing failed: {str(exc)[:400]}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    # Save mart to datasets/marts
    from app.services.mart_service import MARTS_DIR
    MARTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = mart["datasetSlug"]
    mart_filename = f"{slug}.json"
    mart_path = MARTS_DIR / mart_filename
    mart_path.write_text(json.dumps(mart, indent=2, ensure_ascii=False), encoding="utf-8")

    # Also copy to frontend public data directory
    target_dir = PROJECT_ROOT / "frontend" / "public" / "data"
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / mart_filename).write_text(
        json.dumps(mart, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    write_audit_log(
        "csv_dataset_upload",
        "completed",
        f"Uploaded and converted CSV dataset '{name}' ({mart['overview']['totalRecords']:,} records).",
        {
            "datasetName": name,
            "datasetSlug": slug,
            "filename": file.filename,
            "records": mart["overview"]["totalRecords"],
            "martPath": str(mart_path),
        },
    )
    return {
        "status": "created",
        "datasetName": name,
        "datasetSlug": slug,
        "filename": mart_filename,
        "records": mart["overview"]["totalRecords"],
        "qualityScore": mart["overview"]["warehouseQualityScore"],
        "martPath": str(mart_path),
    }


@app.get("/events")
def events() -> list[dict[str, Any]]:
    return load_mart()["events"]


@app.get("/events/{event_id}")
def event_detail(event_id: str) -> dict[str, Any]:
    mart = load_mart()
    event = next((item for item in mart["events"] if item["id"] == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    narratives = [item for item in mart["narratives"] if item["eventId"] == event_id]
    return {"event": event, "narratives": narratives}


@app.get("/narratives")
def narratives() -> list[dict[str, Any]]:
    return load_mart()["narratives"]


@app.get("/narratives/trending")
def trending_narratives() -> list[dict[str, Any]]:
    return load_mart()["topGrowingTopics"]


@app.get("/entities")
def entities() -> list[dict[str, Any]]:
    return load_mart()["entities"]


@app.get("/entities/top")
def top_entities() -> list[dict[str, Any]]:
    return load_mart()["entities"][:10]


@app.get("/sentiment")
def sentiment() -> dict[str, Any]:
    mart = load_mart()
    return {
        "distribution": mart["overview"]["sentimentDistribution"],
        "timeline": mart["sentimentTimeline"],
    }


@app.get("/predictions")
def predictions() -> list[dict[str, Any]]:
    return load_mart()["predictions"]


@app.get("/graph")
def graph() -> dict[str, Any]:
    return load_mart()["graph"]


@app.get("/reports/summary")
def report_summary() -> dict[str, Any]:
    return load_mart()["reportSummary"]


@app.post("/reports/export/pdf")
def export_report_pdf(
    dataset_slug: str | None = Query(default=None),
    live_query: str | None = Query(default=None),
) -> dict[str, Any]:
    import tempfile

    temp_file_path = None
    mart_file_to_use = DEFAULT_MART

    if live_query:
        try:
            live_mart = generate_live_mart_data(live_query.strip())
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
                tmp.write(json.dumps(live_mart, indent=2, ensure_ascii=False).encode("utf-8"))
                temp_file_path = Path(tmp.name)
            mart_file_to_use = temp_file_path
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Failed to generate live mart report data: {exc}") from exc
    elif dataset_slug:
        from app.services.mart_service import MARTS_DIR
        slug_file = MARTS_DIR / f"{dataset_slug}.json"
        if slug_file.exists():
            mart_file_to_use = slug_file
        else:
            raise HTTPException(status_code=404, detail=f"Dataset slug '{dataset_slug}' not found.")

    try:
        gen_cmd = [sys.executable, str(REPORT_GENERATOR), "--mart", str(mart_file_to_use)]
        html_result = command_result(gen_cmd, timeout=120)
        if html_result["returnCode"] != 0:
            write_audit_log(
                "report_pdf_export",
                "failed",
                "HTML report generation failed before PDF export.",
                {"returnCode": html_result["returnCode"], "stderr": html_result["stderr"][:500]},
            )
            raise HTTPException(status_code=500, detail=html_result["stderr"] or "HTML report generation failed.")

        pdf_result = command_result([sys.executable, str(REPORT_PDF_EXPORTER)], timeout=120)
        if pdf_result["returnCode"] != 0:
            write_audit_log(
                "report_pdf_export",
                "failed",
                "PDF report export command failed.",
                {"returnCode": pdf_result["returnCode"], "stderr": pdf_result["stderr"][:500]},
            )
            raise HTTPException(status_code=500, detail=pdf_result["stderr"] or "PDF report export failed.")
        if not REPORT_PDF.exists():
            write_audit_log("report_pdf_export", "failed", "PDF export finished but the PDF artifact was missing.")
            raise HTTPException(status_code=500, detail="PDF export completed, but the PDF file was not found.")

        write_audit_log(
            "report_pdf_export",
            "completed",
            "Generated branded exhibition PDF report.",
            {
                "htmlPath": str(REPORT_HTML),
                "pdfPath": str(REPORT_PDF),
                "pdfBytes": REPORT_PDF.stat().st_size,
                "durationSeconds": round(html_result["durationSeconds"] + pdf_result["durationSeconds"], 2),
            },
        )
        return {
            "status": "generated",
            "htmlPath": str(REPORT_HTML),
            "pdfPath": str(REPORT_PDF),
            "pdfBytes": REPORT_PDF.stat().st_size,
            "downloadUrl": "/reports/download/pdf",
            "htmlUrl": "/reports/download/html",
            "result": pdf_result,
        }
    finally:
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception:
                pass


@app.get("/reports/download/{kind}")
def download_report(
    kind: str,
    dataset_slug: str | None = Query(default=None),
    live_query: str | None = Query(default=None),
) -> FileResponse:
    normalized = kind.lower()

    if normalized == "html" and (dataset_slug or live_query):
        import tempfile
        temp_file_path = None
        mart_file_to_use = DEFAULT_MART

        if live_query:
            try:
                live_mart = generate_live_mart_data(live_query.strip())
                with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
                    tmp.write(json.dumps(live_mart, indent=2, ensure_ascii=False).encode("utf-8"))
                    temp_file_path = Path(tmp.name)
                mart_file_to_use = temp_file_path
            except Exception as exc:
                raise HTTPException(status_code=422, detail=f"Failed to generate live mart report: {exc}") from exc
        elif dataset_slug:
            from app.services.mart_service import MARTS_DIR
            slug_file = MARTS_DIR / f"{dataset_slug}.json"
            if slug_file.exists():
                mart_file_to_use = slug_file

        try:
            gen_cmd = [sys.executable, str(REPORT_GENERATOR), "--mart", str(mart_file_to_use)]
            command_result(gen_cmd, timeout=120)
        finally:
            if temp_file_path and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except Exception:
                    pass

    if normalized == "pdf":
        path = REPORT_PDF
        media_type = "application/pdf"
        filename = "narrativeiq_exhibition_report.pdf"
    elif normalized == "html":
        path = REPORT_HTML
        media_type = "text/html"
        filename = "narrativeiq_exhibition_report.html"
    else:
        raise HTTPException(status_code=404, detail="Report format not found.")

    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} has not been generated yet.")
    write_audit_log(
        "report_download",
        "served",
        f"Served {normalized.upper()} report artifact.",
        {"filename": filename, "bytes": path.stat().st_size},
    )
    return FileResponse(path, media_type=media_type, filename=filename)


@app.get("/etl/quality")
def etl_quality() -> list[dict[str, Any]]:
    return load_mart()["dataQuality"]


@app.get("/topic-intelligence")
def topic_intelligence(
    q: str = Query(default="Artificial Intelligence", min_length=2, max_length=120),
    live: bool = Query(default=True),
) -> dict[str, Any]:
    query = q.strip()
    if live:
        live_profile = live_topic_profile(query)
        if live_profile:
            return live_profile
    return nearest_topic_profile(load_mart(), query)


@app.post("/topic-intelligence/save")
def save_topic_intelligence(brief: dict[str, Any] = Body(...)) -> dict[str, Any]:
    if not postgres_configured():
        write_audit_log(
            "topic_snapshot_save",
            "failed",
            "Live topic snapshot save was requested before PostgreSQL was configured.",
            {"topic": brief.get("query")},
        )
        raise HTTPException(status_code=400, detail="PostgreSQL is not configured.")
    try:
        result = save_topic_brief(brief)
        write_audit_log(
            "topic_snapshot_save",
            "completed",
            f"Saved live topic snapshot for {brief.get('query', 'untitled topic')}.",
            {
                "topic": brief.get("query"),
                "snapshotKey": result.get("snapshotKey"),
                "sourcesSaved": result.get("sourcesSaved"),
                "confidence": brief.get("confidence"),
            },
        )
        return result
    except Exception as exc:
        write_audit_log(
            "topic_snapshot_save",
            "failed",
            f"Live topic snapshot save failed: {str(exc)[:220]}",
            {"topic": brief.get("query")},
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/topic-intelligence/saved")
def saved_topic_intelligence(limit: int = Query(default=8, ge=1, le=25)) -> dict[str, Any]:
    if not postgres_configured():
        return {"postgresConfigured": False, "snapshots": []}
    try:
        return {"postgresConfigured": True, "snapshots": list_saved_topic_briefs(limit)}
    except Exception as exc:
        return {
            "postgresConfigured": False,
            "snapshots": [],
            "error": f"Database connection failed: {str(exc)}"
        }


@app.get("/topic-intelligence/saved/{snapshot_key}")
def saved_topic_intelligence_detail(snapshot_key: int) -> dict[str, Any]:
    if not postgres_configured():
        raise HTTPException(status_code=400, detail="PostgreSQL is not configured.")
    try:
        return saved_topic_brief(snapshot_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/admin/status")
def admin_status() -> dict[str, Any]:
    mart = load_mart()
    return {
        "generatedAt": mart["generatedAt"],
        "historicalThrough": mart["historicalThrough"],
        "records": mart["overview"]["totalRecords"],
        "warehouseQualityScore": mart["overview"]["warehouseQualityScore"],
        "warehouseStats": mart["warehouseStats"],
        "warehouseFiles": warehouse_file_stats(),
        "postgresConfigured": postgres_configured(),
        "databaseHint": "Set NARRATIVEIQ_DATABASE_URL or DATABASE_URL to enable PostgreSQL loading.",
    }


@app.get("/admin/audit-log")
def admin_audit_log(limit: int = Query(default=12, ge=1, le=50)) -> dict[str, Any]:
    return read_audit_log(limit)


@app.post("/admin/import/source-pack")
def admin_import_source_pack(payload: dict[str, Any] = Body(...), admin_key: None = Depends(require_admin_key)) -> dict[str, Any]:
    try:
        return import_source_pack(payload)
    except ValueError as exc:
        write_audit_log(
            "source_pack_import",
            "failed",
            f"Source pack import failed: {str(exc)}",
            {"name": payload.get("name"), "sourceType": payload.get("sourceType")},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        write_audit_log(
            "source_pack_import",
            "failed",
            f"Source pack import failed unexpectedly: {str(exc)[:220]}",
            {"name": payload.get("name"), "sourceType": payload.get("sourceType")},
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/admin/etl/run")
def run_etl(
    records: int = Query(default=50_000, ge=1, le=1_000_000),
    dataset_name: str = Query(default="NarrativeIQ Warehouse", max_length=80),
    admin_key: None = Depends(require_admin_key),
) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(PIPELINE_SCRIPT),
        "--records", str(records),
        "--dataset-name", dataset_name,
    ]
    result = command_result(cmd, timeout=240)
    clear_mart_cache()
    mart = load_mart()
    status = "completed" if result["returnCode"] == 0 else "failed"
    payload = {
        "status": status,
        "result": result,
        "records": mart["overview"]["totalRecords"],
        "generatedAt": mart["generatedAt"],
        "warehouseQualityScore": mart["overview"]["warehouseQualityScore"],
        "datasetName": dataset_name,
    }
    write_audit_log(
        "etl_run",
        status,
        f"ETL run {status} for {records:,} requested records — dataset: '{dataset_name}'.",
        {
            "returnCode": result["returnCode"],
            "durationSeconds": result["durationSeconds"],
            "records": payload["records"],
            "warehouseQualityScore": payload["warehouseQualityScore"],
            "datasetName": dataset_name,
        },
    )
    return payload


@app.post("/admin/warehouse/load")
def load_warehouse(dry_run: bool = Query(default=False), admin_key: None = Depends(require_admin_key)) -> dict[str, Any]:
    command = [sys.executable, str(WAREHOUSE_LOADER)]
    if dry_run:
        command.append("--dry-run")
    result = command_result(command, timeout=300)
    status = "completed" if result["returnCode"] == 0 else "failed"
    action = "warehouse_load_check" if dry_run else "warehouse_load"
    payload = {
        "status": status,
        "postgresConfigured": postgres_configured(),
        "result": result,
    }
    write_audit_log(
        action,
        status,
        ("Warehouse loader dry run " if dry_run else "Warehouse PostgreSQL load ") + status + ".",
        {
            "returnCode": result["returnCode"],
            "durationSeconds": result["durationSeconds"],
            "postgresConfigured": payload["postgresConfigured"],
        },
    )
    return payload


@app.post("/admin/enrichment/run")
def run_enrichment(
    importId: str = Query(...),
    model: str = Query(default="deepseek-chat"),
    admin_key: None = Depends(require_admin_key),
) -> dict[str, Any]:
    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)
    import_file = IMPORT_DIR / f"{importId}.json"
    if not import_file.exists():
        raise HTTPException(status_code=404, detail=f"Import pack {importId} not found.")
    
    try:
        import_data = json.loads(import_file.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read import pack: {str(exc)}")
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        write_audit_log(
            "deepseek_enrichment",
            "failed",
            "DeepSeek enrichment failed: DEEPSEEK_API_KEY is not configured.",
            {"importId": importId}
        )
        raise HTTPException(status_code=400, detail="DEEPSEEK_API_KEY environment variable is not configured.")
    
    try:
        from etl.deepseek_enrichment import enrich_import_artifact
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load DeepSeek enrichment module: {str(exc)}")
    
    try:
        enriched_artifact = enrich_import_artifact(import_data, api_key=api_key, model=model)
        enriched_file = ENRICHED_DIR / f"{importId}.json"
        enriched_file.write_text(json.dumps(enriched_artifact, ensure_ascii=False, indent=2), encoding="utf-8")
        
        write_audit_log(
            "deepseek_enrichment",
            "completed",
            f"Enriched source pack {import_data.get('name', importId)} with {enriched_artifact.get('enrichedCount', 0)} rows.",
            {
                "importId": importId,
                "model": model,
                "enrichedCount": enriched_artifact.get("enrichedCount", 0),
                "enrichedPath": str(enriched_file)
            }
        )
        return {
            "status": "enriched",
            "importId": importId,
            "enrichedCount": enriched_artifact.get("enrichedCount", 0),
            "artifactPath": str(enriched_file)
        }
    except Exception as exc:
        write_audit_log(
            "deepseek_enrichment",
            "failed",
            f"DeepSeek enrichment failed: {str(exc)[:220]}",
            {"importId": importId}
        )
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/admin/ingestion/schedule")
def update_schedule(
    interval_minutes: int = Query(..., ge=0, le=10080),
    enabled: bool = Query(True),
    admin_key: None = Depends(require_admin_key),
) -> dict[str, Any]:
    try:
        save_scheduler_config(interval_minutes, enabled)
        scheduler_state.enabled = enabled
        scheduler_state.interval_minutes = interval_minutes
        
        if enabled and interval_minutes > 0:
            from datetime import datetime, timedelta
            scheduler_state.next_run = (datetime.utcnow() + timedelta(minutes=interval_minutes)).isoformat() + "Z"
        else:
            scheduler_state.next_run = None

        write_audit_log(
            "ingestion_schedule_update",
            "completed",
            f"Ingestion schedule updated: interval={interval_minutes}m, enabled={enabled}."
        )
        
        topics = get_all_saved_topic_names()
        if not topics:
            topics = ["Artificial Intelligence"]
            
        return {
            "postgresConfigured": postgres_configured(),
            "enabled": scheduler_state.enabled,
            "intervalMinutes": scheduler_state.interval_minutes,
            "lastRunTime": scheduler_state.last_run,
            "lastRunAt": scheduler_state.last_run,
            "nextRunTime": scheduler_state.next_run,
            "nextRunAt": scheduler_state.next_run,
            "countOfAutoRefreshedTopics": scheduler_state.refreshed_count,
            "runCount": scheduler_state.refreshed_count,
            "topics": topics,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/admin/ingestion/status")
def get_schedule_status() -> dict[str, Any]:
    topics = get_all_saved_topic_names()
    if not topics:
        topics = ["Artificial Intelligence"]
    return {
        "postgresConfigured": postgres_configured(),
        "enabled": scheduler_state.enabled,
        "intervalMinutes": scheduler_state.interval_minutes,
        "lastRunTime": scheduler_state.last_run,
        "lastRunAt": scheduler_state.last_run,
        "nextRunTime": scheduler_state.next_run,
        "nextRunAt": scheduler_state.next_run,
        "countOfAutoRefreshedTopics": scheduler_state.refreshed_count,
        "runCount": scheduler_state.refreshed_count,
        "topics": topics,
    }


def generate_live_mart_data(query: str) -> dict[str, Any]:
    profile = live_topic_profile(query)
    if not profile:
        profile = nearest_topic_profile(load_mart(), query)
    else:
        # Automatically save the live search brief to the PostgreSQL database if configured
        if profile.get("mode") != "warehouse_match" and postgres_configured():
            try:
                save_topic_brief(profile)
            except Exception as e:
                write_audit_log(
                    "live_search_auto_save",
                    "failed",
                    f"Failed to auto-save live search '{query}' to database: {str(e)[:200]}"
                )

    # Build a minimal mart that the frontend can consume in exactly the same way
    # as the warehouse mart, ensuring every section (Events, Entities, Sentiment,
    # Replay, Predictions, Graph) renders live data.
    from datetime import datetime as _dt

    now_iso = _dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    event = profile["event"]
    narratives = profile["narratives"]
    entities = profile["entities"]
    timeline = profile["timeline"]
    sentiment_dist = profile["sentimentDistribution"]
    mode = profile["mode"]

    # Sentiment timeline — one row per month in the topic timeline
    sentiment_timeline = [
        {
            "date": point["month"] + "-01",
            "positive": int(round(max(0, point.get("sentiment", 0)) * 180 + 60)),
            "neutral": 80,
            "negative": int(round(max(0, -point.get("sentiment", 0)) * 160 + 40)),
        }
        for point in timeline
    ]

    # Replay frames — each month becomes one replay frame
    replay_frames = [
        {
            "date": point["month"] + "-01",
            "label": point["month"],
            "dominantNarrative": narratives[0]["topic"] if narratives else query,
            "stage": narratives[0]["lifecycleStage"] if narratives else "Emerging",
            "strength": point["strength"],
            "sentiment": point.get("sentiment", 0),
            "activeNarratives": [
                {
                    "topic": n["topic"],
                    "strength": round(point["strength"] * (1 - 0.12 * i), 2),
                    "stage": n["lifecycleStage"],
                }
                for i, n in enumerate(narratives[:3])
            ],
        }
        for point in timeline
    ]

    # Knowledge graph from entities
    nodes = [
        {
            "id": f"entity-{i}",
            "label": e["name"],
            "type": e.get("type", "Entity"),
            "score": round(e.get("mentionStrength", 50), 2),
        }
        for i, e in enumerate(entities[:10])
    ]
    # Topic node
    nodes.insert(0, {"id": "topic-0", "label": query, "type": "Topic", "score": round(profile["narrativeStrength"], 2)})
    links = [
        {"source": "topic-0", "target": f"entity-{i}", "type": "mentions", "strength": round(e.get("mentionStrength", 50) / 100, 2)}
        for i, e in enumerate(entities[:10])
    ]

    # Predictions — linear extrapolation of the last 3 timeline points for each narrative
    predictions = []
    for index, n in enumerate(narratives[:3]):
        n_timeline = n["timeline"]
        n_last_strength = n_timeline[-1]["strength"] if n_timeline else 50
        n_growth = (n_timeline[-1]["strength"] - n_timeline[-3]["strength"]) / 2 if len(n_timeline) >= 3 else 2
        predictions.append(
            {
                "narrative": n["topic"],
                "eventName": event["name"],
                "expectedGrowth": round(n_growth, 2),
                "direction": "Rising" if n_growth > 0 else "Declining",
                "forecast": [
                    {
                        "period": f"+{m}M",
                        "strength": round(min(100, max(1, n_last_strength + n_growth * m)), 2),
                        "confidence": round(max(40, profile["confidence"] - m * 4), 2),
                    }
                    for m in range(1, 7)
                ],
            }
        )

    # Intelligence feed from sources
    sources = profile.get("sources") or []
    feed = [
        {
            "title": s.get("title", "Untitled source"),
            "body": f"Source: {s.get('domain', 'unknown')} · {s.get('publishedAt', 'recent')} · {s.get('type', 'News')}",
            "severity": "High" if i < 2 else "Medium" if i < 5 else "Low",
        }
        for i, s in enumerate(sources[:6])
    ]
    if not feed:
        feed = [{"title": f"{query} — live intelligence brief", "body": profile["summary"][:180], "severity": "High"}]

    # Data quality rows
    total_signals = (profile.get("evidence") or {}).get("totalSignals", 0)
    data_quality = [
        {
            "dataset": "live_topic_signals",
            "record_count": total_signals,
            "completeness": round(min(100, profile["confidence"]), 2),
            "uniqueness": 98.0,
            "consistency": round(min(100, 75 + profile["confidence"] * 0.25), 2),
            "timeliness": 100.0,
            "quality_score": round(min(100, profile["confidence"]), 2),
        },
        {
            "dataset": "live_news_articles",
            "record_count": (profile.get("evidence") or {}).get("newsSignals", 0),
            "completeness": 95.0,
            "uniqueness": 99.0,
            "consistency": 90.0,
            "timeliness": 100.0,
            "quality_score": 95.0,
        },
    ]

    return {
        "generatedAt": now_iso,
        "historicalThrough": now_iso[:10],
        "liveMode": True,
        "liveQuery": query,
        "liveSourceMode": mode,
        "overview": {
            "totalRecords": total_signals,
            "activeEvents": 1,
            "activeNarratives": len(narratives),
            "narrativeHealthScore": round(profile["narrativeStrength"], 2),
            "warehouseQualityScore": round(profile["confidence"], 2),
            "sentimentDistribution": [
                {"label": item["label"], "value": item["value"]}
                for item in sentiment_dist
            ],
        },
        "warehouseStats": {
            "dimensions": {"dim_live_topic": 1, "dim_source": len(sources)},
            "facts": {"fact_signals": total_signals, "fact_articles": len(sources)},
        },
        "events": [event],
        "narratives": narratives,
        "topGrowingTopics": [
            {"topic": n["topic"], "eventName": event["name"], "trendScore": n["latestStrength"], "growthRate": n["growthRate"], "momentum": n["influenceScore"]}
            for n in narratives
        ],
        "entities": entities,
        "sentimentTimeline": sentiment_timeline,
        "predictions": predictions,
        "graph": {"nodes": nodes, "links": links},
        "replayFrames": replay_frames,
        "dataQuality": data_quality,
        "intelligenceFeed": feed,
        "reportSummary": {
            "title": f"Live Topic Brief: {query}",
            "eventFocus": event["name"],
            "period": f"{timeline[0]['month'] if timeline else 'N/A'} – {now_iso[:7]}",
            "primaryFinding": profile["summary"][:280],
            "recommendedDemoFlow": profile.get("recommendedActions", []),
        },
    }


@app.get("/topic-intelligence/live-mart")
def topic_live_mart(
    q: str = Query(default="Artificial Intelligence", min_length=2, max_length=120),
) -> dict[str, Any]:
    """
    Returns a full NarrativeMart-compatible snapshot synthesised entirely from
    live sources (Wikipedia + GDELT + Google News RSS) for the given query.
    When a topic is found live this powers all dashboard sections in Live Mode.
    Falls back to the nearest warehouse match if live sources are unavailable.
    """
    return generate_live_mart_data(q.strip())


