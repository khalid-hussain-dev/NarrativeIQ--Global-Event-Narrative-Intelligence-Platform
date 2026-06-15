# NarrativeIQ Group Member Roles

Date: 2026-06-09

This document divides NarrativeIQ into exhibition ownership areas for a four-member group. The distribution is intentionally not perfectly equal. Khalid has the largest scope, Umsa has the second largest scope, and Zilehuma and Laiqa have similar supporting scopes.

Recommended responsibility split:

| Member | Role | Approximate Scope |
| --- | --- | ---: |
| Khalid | Project Lead, Data Warehouse, Backend, Integration | 38% |
| Umsa | Frontend Dashboard, Visual Analytics, User Flow | 26% |
| Zilehuma | Documentation, Reporting, Topic IQ Explanation, Exhibition Story | 18% |
| Laiqa | ETL, Dataset, Data Quality, Warehouse Explanation | 18% |

## 1. Khalid

Role title:

Project Lead, Data Warehouse, Backend, and Integration Lead

Main responsibility:

Khalid owns the overall technical architecture and the main warehouse-to-dashboard integration. He should be the primary person to explain how NarrativeIQ works internally.

Work areas:

- Finalized the project idea and aligned it with the original NarrativeIQ blueprint.
- Managed the overall architecture:
  - ETL layer
  - data warehouse layer
  - PostgreSQL loading
  - FastAPI backend
  - Next.js frontend integration
- Worked on the warehouse-first structure.
- Designed and explained the star-schema approach.
- Connected backend APIs with dashboard modules.
- Configured PostgreSQL environment for local demo.
- Verified the one-command demo startup.
- Handled admin controls for ETL and warehouse loading.
- Oversaw saved Topic IQ snapshots in PostgreSQL.
- Oversaw final project completion tracking.

Modules Khalid should explain:

- Project architecture.
- ETL to warehouse to dashboard flow.
- PostgreSQL configuration.
- FastAPI endpoints.
- Admin panel.
- Live Topic IQ saving into PostgreSQL.
- Difference between exhibition version and final version.

Files or folders Khalid should know:

- `etl/pipeline.py`
- `etl/load_postgres.py`
- `warehouse/001_schema.sql`
- `warehouse/002_materialized_views.sql`
- `warehouse/003_live_topic_schema.sql`
- `backend/app/main.py`
- `scripts/start_demo.ps1`
- `.env`

Exhibition talking points:

- "NarrativeIQ is warehouse-first. We do not start from dashboard cards; we start from ETL, warehouse tables, facts, dimensions, and marts."
- "The main dashboard uses a deterministic 50,000-record exhibition mart, while Topic IQ adds lightweight live public-source metadata."
- "Saved Topic IQ briefs are persisted into PostgreSQL through live-topic dimension and fact tables."
- "The admin module proves operational control: ETL, warehouse load, PostgreSQL status, and audit logs."

Likely viva questions Khalid can answer:

- What is the complete architecture?
- Why did we use PostgreSQL?
- What is the difference between fact and dimension tables?
- How does Topic IQ save data?
- What is real and what is simulated?
- How is the warehouse connected to the dashboard?

## 2. Umsa

Role title:

Frontend Dashboard, Visual Analytics, and User Experience Lead

Main responsibility:

Umsa owns the dashboard experience and the visual analytics modules. She should explain how users interact with the project and how insights are displayed.

Work areas:

- Worked on the Next.js dashboard structure.
- Helped organize the drawer navigation and dashboard sections.
- Worked on the visual presentation of:
  - Overview
  - Topic IQ
  - Events
  - Sentiment
  - Replay
  - Compare
  - Graph
  - Predictions
  - Reports
  - Administration
- Improved dashboard usability for exhibition flow.
- Handled search flow and navigation behavior.
- Worked on the hamburger drawer and scrollable navigation.
- Helped improve report export buttons and status messages.
- Worked on responsive behavior for laptop and mobile screens.
- Helped implement visual graph controls:
  - zoom
  - pan
  - fit view
  - selected-node focus
  - neighborhood expansion

Modules Umsa should explain:

- Dashboard overview.
- Drawer navigation.
- Topic IQ interface.
- Search bar behavior.
- Narrative replay.
- Narrative comparison.
- Knowledge graph controls.
- Reports UI.
- Responsive design.

Files or folders Umsa should know:

- `frontend/src/components/DashboardApp.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/components/Logo.tsx`
- `frontend/src/types/intelligence.ts`
- `frontend/src/data/narrativeiq_mart.json`

Exhibition talking points:

- "The dashboard is not just static UI; it reads from FastAPI when the backend is running and falls back to bundled mart data if needed."
- "The drawer makes all intelligence modules accessible in one workflow."
- "The graph supports zoom, pan, fit view, focus, and expansion to make relationship exploration interactive."
- "Reports can be exported as PDF, HTML, or CSV."

Likely viva questions Umsa can answer:

- How does the user navigate the system?
- What happens when a topic is searched?
- What is the purpose of the graph?
- How does narrative comparison work visually?
- How do reports get exported?

## 3. Zilehuma

Role title:

Documentation, Reporting, Topic IQ, and Exhibition Presentation Lead

Main responsibility:

Zilehuma owns the documentation and presentation side, with special focus on explaining the project idea, reports, Topic IQ behavior, and final vs exhibition scope.

Work areas:

- Worked on project documentation and exhibition explanation.
- Helped prepare the project proposal.
- Helped compare the exhibition version with the final project version.
- Worked on explaining the original project vision from the provided documents.
- Helped organize the judge-facing demo flow.
- Focused on Topic IQ explanation:
  - live public-source metadata
  - confidence score
  - source clusters
  - saved brief history
- Helped explain generated reports:
  - HTML
  - PDF
  - CSV
- Helped explain logo placement and branding.
- Helped prepare answers for what is implemented and what is future work.

Modules Zilehuma should explain:

- Project description.
- Problem statement.
- Topic IQ live search.
- Report generation.
- Exhibition version vs final version.
- Logo and branding.
- Demo flow.
- Future scope.

Files or folders Zilehuma should know:

- `README.md`
- `docs/EXHIBITION_DEMO_FLOW.md`
- `docs/FINAL_COMPLETION_AUDIT.md`
- `docs/submission_2026_06_09/PROJECT_PROPOSAL.md`
- `docs/submission_2026_06_09/EXHIBITION_VS_FINAL_COMPARISON.md`
- `reports/generated/`
- `Logo.png`

Exhibition talking points:

- "NarrativeIQ is designed to understand public narratives, not just count trends."
- "Topic IQ allows users to search any topic and receive an intelligence-style brief."
- "The current exhibition version is complete, while the final production version would add scheduled ingestion, auth, tests, and deeper AI enrichment."
- "Reports make the dashboard findings exportable and presentation-ready."

Likely viva questions Zilehuma can answer:

- What problem does NarrativeIQ solve?
- What are the main features?
- How is the project useful?
- What is the difference between exhibition MVP and final project?
- What does Topic IQ do?
- What future improvements are planned?

## 4. Laiqa

Role title:

ETL, Dataset, Data Quality, and Warehouse Explanation Lead

Main responsibility:

Laiqa owns the data preparation and DW&BD explanation side. She should explain how the dataset is produced, cleaned, transformed, and validated.

Work areas:

- Worked on understanding and documenting the 50,000-record generated dataset.
- Helped map project data into event, topic, entity, sentiment, and source structures.
- Focused on ETL explanation:
  - extract
  - transform
  - load
- Helped explain dimension and fact table usage.
- Worked on the data quality dashboard explanation.
- Helped verify that warehouse files are generated correctly.
- Helped explain why deterministic data is used for exhibition stability.
- Prepared explanations for:
  - synthetic data
  - live metadata
  - saved PostgreSQL snapshots
  - mart data

Modules Laiqa should explain:

- ETL pipeline.
- Generated dataset.
- Warehouse CSV files.
- Data quality profiling.
- Dimension tables.
- Fact tables.
- Materialized views.
- Marts.

Files or folders Laiqa should know:

- `etl/pipeline.py`
- `datasets/warehouse/`
- `datasets/marts/narrativeiq_mart.json`
- `warehouse/001_schema.sql`
- `warehouse/002_materialized_views.sql`
- `docs/DWBD_CONCEPTS.md`
- `docs/submission_2026_06_09/DWBD_CONCEPTS_GUIDE.md`

Exhibition talking points:

- "ETL is the backbone of the project. It converts raw/generated signals into structured warehouse tables."
- "Dimension tables store context, while fact tables store measurable values."
- "Data quality metrics prove that the ETL outputs are reliable for analysis."
- "The mart is prepared from warehouse-style data so the dashboard does not depend on hard-coded values."

Likely viva questions Laiqa can answer:

- What is ETL?
- What are fact tables?
- What are dimension tables?
- Why did we use a star schema?
- What does data quality mean in this project?
- What is the difference between warehouse data and mart data?

## Recommended Presentation Flow By Member

1. Zilehuma starts with the project idea, title, problem statement, and purpose.
2. Khalid explains architecture, backend, warehouse, and PostgreSQL.
3. Laiqa explains ETL, dataset, fact/dimension tables, data quality, and marts.
4. Umsa demonstrates dashboard modules, graph, replay, comparison, reports, and user flow.
5. Khalid closes with current completion, final-version pending work, and technical strengths.

## Important Coordination Notes

- Khalid should be ready for deep technical questions.
- Umsa should be ready to operate the dashboard confidently.
- Zilehuma should be ready to explain the proposal, motivation, documentation, and future scope.
- Laiqa should be ready to explain DW&BD concepts simply.
- All members should know the difference between deterministic exhibition data and live Topic IQ metadata.
- All members should avoid saying the dashboard is only dummy UI. It is backed by ETL-generated mart data and FastAPI, with live Topic IQ and PostgreSQL persistence.
