# NarrativeIQ Implementation Notes

## Build Principle

NarrativeIQ follows the project blueprint rule: warehouse first, dashboards second. The frontend consumes generated marts that are produced by the ETL pipeline from warehouse-style data outputs.

## Sprint 0 and Sprint 1 Scope

This first build establishes:

- Standard repository layout.
- Logo asset variants for full, nav, icon, dashboard, reports, and README usage.
- PostgreSQL star schema DDL.
- Deterministic synthetic exhibition dataset.
- Warehouse-style CSV dimensions and facts.
- FastAPI API contracts matching the project context.
- Next.js dashboard shell with overview, replay, graph, prediction, quality, and report sections.
- Administration controls for ETL refresh and warehouse load checks.
- PostgreSQL loader using generated CSV outputs and `psql`.

## Demo Dataset

The default ETL creates four event packs:

- Artificial Intelligence Revolution
- Cricket World Cup
- Global Elections
- Natural Disaster Response

Historical observations run through June 2026. Prediction outputs are intentionally separated from historical marts.

## API Surface

The backend exposes:

- `GET /health`
- `GET /dashboard`
- `GET /events`
- `GET /events/{event_id}`
- `GET /narratives`
- `GET /narratives/trending`
- `GET /entities`
- `GET /entities/top`
- `GET /sentiment`
- `GET /predictions`
- `GET /graph`
- `GET /reports/summary`
- `GET /etl/quality`
- `GET /admin/status`
- `POST /admin/etl/run`
- `POST /admin/warehouse/load`

## Next Steps

The next sprint should add authentication/roles for the Administration module, then replace synchronous job execution with a background job queue and persisted job audit logs.
