from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE_DIR = ROOT / "datasets" / "warehouse"
SCHEMA_SQL = ROOT / "warehouse" / "001_schema.sql"
MATERIALIZED_SQL = ROOT / "warehouse" / "002_materialized_views.sql"


@dataclass(frozen=True)
class CopySpec:
    table: str
    csv_file: str
    columns: tuple[str, ...]


COPY_ORDER: tuple[CopySpec, ...] = (
    CopySpec("dim_date", "dim_date.csv", ("date_key", "full_date", "day", "week", "month", "quarter", "year")),
    CopySpec("dim_source", "dim_source.csv", ("source_key", "source_id", "source_name", "source_type", "platform")),
    CopySpec("dim_event", "dim_event.csv", ("event_key", "event_id", "event_name", "event_category", "region", "start_date", "end_date")),
    CopySpec("dim_entity", "dim_entity.csv", ("entity_key", "entity_name", "entity_type")),
    CopySpec("dim_topic", "dim_topic.csv", ("topic_key", "topic_name", "topic_category")),
    CopySpec("dim_sentiment", "dim_sentiment.csv", ("sentiment_key", "sentiment_label")),
    CopySpec("fact_content", "fact_content.csv", ("content_key", "date_key", "source_key", "event_key", "topic_key", "sentiment_key", "engagement_score", "reach_score", "popularity_score")),
    CopySpec("fact_sentiment", "fact_sentiment.csv", ("sentiment_fact_key", "date_key", "event_key", "sentiment_key", "sentiment_score", "polarity", "content_count")),
    CopySpec("fact_entity_mentions", "fact_entity_mentions.csv", ("mention_key", "entity_key", "event_key", "date_key", "mention_count", "mention_strength")),
    CopySpec("fact_narrative", "fact_narrative.csv", ("narrative_fact_key", "date_key", "topic_key", "event_key", "narrative_strength", "growth_rate", "influence_score", "lifecycle_stage")),
    CopySpec("fact_trends", "fact_trends.csv", ("trend_key", "date_key", "topic_key", "event_key", "trend_score", "growth_rate", "momentum")),
    CopySpec("entity_relationships", "entity_relationships.csv", ("relationship_key", "source_entity_key", "target_entity_key", "relationship_type", "strength_score")),
)


TRUNCATE_SQL = """
SET search_path TO narrativeiq;
TRUNCATE TABLE
    fact_content,
    fact_sentiment,
    fact_entity_mentions,
    fact_narrative,
    fact_trends,
    entity_relationships,
    dim_sentiment,
    dim_topic,
    dim_entity,
    dim_event,
    dim_source,
    dim_date,
    etl_quality_report
RESTART IDENTITY CASCADE;
"""


REFRESH_SQL = """
SET search_path TO narrativeiq;
REFRESH MATERIALIZED VIEW mv_narrative_overview;
REFRESH MATERIALIZED VIEW mv_sentiment_evolution;
REFRESH MATERIALIZED VIEW mv_entity_influence;
REFRESH MATERIALIZED VIEW mv_trend_velocity;
"""


def psql_base_command(database_url: str | None) -> list[str]:
    psql = shutil.which("psql")
    if not psql and sys.platform == "win32":
        for ver in ["17", "16", "15", "14", "13", "12"]:
            candidate = f"C:\\Program Files\\PostgreSQL\\{ver}\\bin\\psql.exe"
            if os.path.exists(candidate):
                psql = candidate
                break
    if not psql:
        raise RuntimeError("psql was not found on PATH. Add PostgreSQL bin directory to PATH or run from a PostgreSQL shell.")
    command = [psql, "-v", "ON_ERROR_STOP=1"]
    if database_url:
        command.extend(["--dbname", database_url])
    return command


def run_psql(database_url: str | None, args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    command = psql_base_command(database_url) + args
    completed = subprocess.run(
        command,
        cwd=ROOT,
        input=input_text,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "psql returned a non-zero exit code."
        raise RuntimeError(detail[-4000:])
    return completed


def copy_sql() -> str:
    lines = ["SET search_path TO narrativeiq;"]
    for spec in COPY_ORDER:
        path = (WAREHOUSE_DIR / spec.csv_file).as_posix()
        columns = ", ".join(spec.columns)
        lines.append(f"\\copy {spec.table} ({columns}) FROM '{path}' WITH (FORMAT csv, HEADER true);")

    quality_path = (WAREHOUSE_DIR / "data_quality_report.csv").as_posix()
    lines.append(
        "\\copy etl_quality_report (dataset, record_count, completeness, uniqueness, consistency, timeliness, quality_score) "
        f"FROM '{quality_path}' WITH (FORMAT csv, HEADER true);"
    )
    return "\n".join(lines) + "\n"


def validate_inputs() -> None:
    missing = [spec.csv_file for spec in COPY_ORDER if not (WAREHOUSE_DIR / spec.csv_file).exists()]
    if not (WAREHOUSE_DIR / "data_quality_report.csv").exists():
        missing.append("data_quality_report.csv")
    if missing:
        raise FileNotFoundError(
            "Missing warehouse CSV outputs: "
            + ", ".join(missing)
            + ". Run `python etl/pipeline.py --records 50000` first."
        )
    if not SCHEMA_SQL.exists() or not MATERIALIZED_SQL.exists():
        raise FileNotFoundError("Warehouse SQL files are missing.")


def load(database_url: str | None, dry_run: bool) -> dict[str, object]:
    validate_inputs()
    psql_base_command(database_url)

    if dry_run:
        return {
            "status": "ready",
            "dryRun": True,
            "tables": [spec.table for spec in COPY_ORDER],
            "warehouseDir": str(WAREHOUSE_DIR),
        }

    run_psql(database_url, ["-f", str(SCHEMA_SQL)])
    run_psql(database_url, ["-f", str(MATERIALIZED_SQL)])
    run_psql(database_url, ["-c", TRUNCATE_SQL])

    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False, encoding="utf-8") as handle:
        handle.write(copy_sql())
        copy_file = Path(handle.name)

    try:
        copy_result = run_psql(database_url, ["-f", str(copy_file)])
    finally:
        copy_file.unlink(missing_ok=True)

    run_psql(database_url, ["-c", REFRESH_SQL])

    return {
        "status": "loaded",
        "dryRun": False,
        "tables": [spec.table for spec in COPY_ORDER],
        "stdout": copy_result.stdout[-4000:],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Load NarrativeIQ generated warehouse CSVs into PostgreSQL.")
    parser.add_argument("--database-url", default=os.getenv("NARRATIVEIQ_DATABASE_URL") or os.getenv("DATABASE_URL"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        result = load(database_url=args.database_url, dry_run=args.dry_run)
    except Exception as exc:
        print(f"Warehouse load failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

    print(result)


if __name__ == "__main__":
    main()
