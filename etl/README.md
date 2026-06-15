# NarrativeIQ ETL

The ETL pipeline creates the exhibition dataset, warehouse-style facts and dimensions, quality profiling output, and API-ready marts.

```powershell
python etl/pipeline.py --records 50000
```

Generated outputs:

- `datasets/raw/raw_content.csv`
- `datasets/event_master.csv`
- `datasets/narrative_history.csv`
- `datasets/sentiment_history.csv`
- `datasets/topic_trends.csv`
- `datasets/entity_mentions.csv`
- `datasets/warehouse/*.csv`
- `datasets/marts/narrativeiq_mart.json`
- `frontend/src/data/narrativeiq_mart.json`
- `frontend/public/data/narrativeiq_mart.json`

Load generated warehouse CSVs into PostgreSQL:

```powershell
$env:NARRATIVEIQ_DATABASE_URL="postgresql://postgres:password@localhost:5432/narrativeiq"
python etl/load_postgres.py --dry-run
python etl/load_postgres.py
```
