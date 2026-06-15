# NarrativeIQ Warehouse

`001_schema.sql` defines the PostgreSQL star schema:

- `dim_date`
- `dim_source`
- `dim_event`
- `dim_entity`
- `dim_topic`
- `dim_sentiment`
- `fact_content`
- `fact_sentiment`
- `fact_entity_mentions`
- `fact_narrative`
- `fact_trends`
- `entity_relationships`
- `etl_quality_report`

`002_materialized_views.sql` adds analytical views for dashboard and API acceleration.

Example:

```powershell
psql -U postgres -d narrativeiq -f warehouse/001_schema.sql
psql -U postgres -d narrativeiq -f warehouse/002_materialized_views.sql
```

Or use the project loader:

```powershell
$env:NARRATIVEIQ_DATABASE_URL="postgresql://postgres:password@localhost:5432/narrativeiq"
python etl/load_postgres.py --dry-run
python etl/load_postgres.py
```

The loader creates the schema, truncates existing warehouse tables, copies generated CSV outputs, and refreshes materialized views.
