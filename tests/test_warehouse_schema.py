from pathlib import Path
import json

WAREHOUSE_DIR = Path(__file__).resolve().parents[1] / "warehouse"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

def test_schema_file_exists():
    assert (WAREHOUSE_DIR / "001_schema.sql").exists()

def test_materialized_views_file_exists():
    assert (WAREHOUSE_DIR / "002_materialized_views.sql").exists()

def test_live_topic_schema_exists():
    assert (WAREHOUSE_DIR / "003_live_topic_schema.sql").exists()

def test_schema_contains_dimension_tables():
    sql = (WAREHOUSE_DIR / "001_schema.sql").read_text(encoding="utf-8").lower()
    for table in ["dim_date", "dim_source", "dim_event", "dim_entity", "dim_topic", "dim_sentiment"]:
        assert table in sql, f"Expected table {table} not found in schema"

def test_schema_contains_fact_tables():
    sql = (WAREHOUSE_DIR / "001_schema.sql").read_text(encoding="utf-8").lower()
    for table in ["fact_content", "fact_sentiment", "fact_entity_mentions", "fact_narrative", "fact_trends"]:
        assert table in sql, f"Expected fact table {table} not found in schema"

def test_materialized_views_defined():
    sql = (WAREHOUSE_DIR / "002_materialized_views.sql").read_text(encoding="utf-8").lower()
    assert "materialized view" in sql or "create materialized" in sql

def test_live_topic_schema_contains_tables():
    sql = (WAREHOUSE_DIR / "003_live_topic_schema.sql").read_text(encoding="utf-8").lower()
    assert "dim_live_topic" in sql
    assert "fact_live_topic_snapshot" in sql

def test_mart_json_exists():
    mart_path = PROJECT_ROOT / "datasets" / "marts" / "narrativeiq_mart.json"
    assert mart_path.exists()

def test_mart_json_structure():
    mart_path = PROJECT_ROOT / "datasets" / "marts" / "narrativeiq_mart.json"
    data = json.loads(mart_path.read_text(encoding="utf-8"))
    for key in ["generatedAt", "overview", "events", "narratives", "entities", "predictions", "graph"]:
        assert key in data, f"Expected mart key {key} not found"
    assert data["overview"]["totalRecords"] > 0
    assert len(data["events"]) > 0
    assert len(data["narratives"]) > 0
