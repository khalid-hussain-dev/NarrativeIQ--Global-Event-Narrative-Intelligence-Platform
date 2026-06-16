# NarrativeIQ — Group Member Roles

**Date:** 2026-06-16 (Final Production Build)
**Live URL:** https://narrativeiq-global-event-narrative.onrender.com/
**Repository:** https://github.com/khalid-hussain-dev/NarrativeIQ--Global-Event-Narrative-Intelligence-Platform

This document divides NarrativeIQ into ownership areas for a four-member group. The distribution reflects actual contribution scope. Khalid has the largest scope, Umsa has the second, and Zilehuma and Laiqa have similar supporting scopes.

| Member | Role | Approximate Scope |
| --- | --- | ---: |
| Khalid | Project Lead, Architecture, Backend, Deployment, Integration | 40% |
| Umsa | Frontend Dashboard, Visual Analytics, UI/UX | 26% |
| Zilehuma | Documentation, Reporting, Topic IQ Explanation, Exhibition Story | 17% |
| Laiqa | ETL, Dataset, Data Quality, Warehouse & DW&BD Concepts | 17% |

---

## 1. Khalid

**Role Title:** Project Lead, Data Warehouse, Backend, Deployment & Integration Lead

**Main Responsibility:**
Khalid owns the overall technical architecture, the unified backend+frontend deployment, and the warehouse-to-dashboard integration. He is the primary person to explain the internal workings of NarrativeIQ.

### Work Areas

- Finalized the project idea and aligned it with the NarrativeIQ blueprint.
- Designed and implemented the complete layered architecture:
  - ETL pipeline (`etl/pipeline.py`)
  - Data warehouse layer (PostgreSQL star schema)
  - FastAPI backend (`backend/app/main.py`)
  - Next.js frontend integration
- Built the warehouse-first structure using dimension and fact tables.
- Designed and deployed the star-schema (6 dimensions, 6 fact tables, 4 materialized views).
- Connected FastAPI API endpoints to the dashboard.
- Implemented the Admin Panel (ETL run, warehouse load, enrichment, audit log, ingestion schedule).
- Built Topic IQ saving into PostgreSQL (`dim_live_topic`, `fact_live_topic_snapshot`, `live_topic_sources`).
- Implemented the background ingestion scheduler (async loop in FastAPI lifespan).
- Implemented DeepSeek AI enrichment integration.
- Built the unified deploy: Next.js static export served directly by FastAPI (single Render service).
- Configured Render deployment with `render_build.sh`, `render.yaml`, Gunicorn + Uvicorn.
- Connected the project to Supabase PostgreSQL (cloud-hosted warehouse).
- Oversaw the entire Git version control and GitHub repository management.
- Fixed admin key validation, CORS configuration, and API URL routing for production.

### Modules Khalid Should Explain

- Complete system architecture and data flow.
- ETL → Warehouse CSVs → PostgreSQL → Materialized Views → Mart JSON → FastAPI → Dashboard.
- PostgreSQL configuration and warehouse schema design.
- All FastAPI endpoints and how they serve the dashboard.
- Admin Panel operations.
- Topic IQ persistence into PostgreSQL.
- Live Ingestion Scheduler behavior.
- DeepSeek AI enrichment pipeline.
- Unified deployment (why both frontend and backend run from a single Render service).
- The difference between exhibition warehouse data and live Topic IQ metadata.

### Key Files Khalid Should Know

- `backend/app/main.py` — FastAPI application, all endpoints, scheduler
- `backend/app/services/mart_service.py` — Mart loading with TTL cache
- `backend/app/services/topic_service.py` — Live topic profiling and PostgreSQL saving
- `backend/app/services/admin_service.py` — Source pack import
- `warehouse/001_schema.sql` — Star schema DDL
- `warehouse/002_materialized_views.sql` — Precomputed analytics views
- `warehouse/003_live_topic_schema.sql` — Live Topic IQ tables
- `etl/pipeline.py` — Full ETL pipeline
- `render.yaml` + `render_build.sh` — Render deployment config
- `scripts/start_demo.ps1` — Local one-command startup

### Exhibition Talking Points

- "NarrativeIQ is warehouse-first. ETL produces data, the warehouse stores it in a star schema, PostgreSQL loads it, and the dashboard reads it through FastAPI."
- "The project is live in production at narrativeiq-global-event-narrative.onrender.com."
- "The entire system runs as one unified service — FastAPI serves both the API and the Next.js UI."
- "Topic IQ performs real live lookups to Wikipedia, GDELT, and Google News, and saves every brief to Supabase PostgreSQL."
- "The admin panel is operational — you can run ETL, load the warehouse, schedule ingestion, and audit every system action in real time."

### Likely Viva Questions Khalid Can Answer

- What is the complete architecture?
- Why did we use PostgreSQL over a simple JSON file?
- What is a materialized view and why use one?
- How does Topic IQ save data to the database?
- What is the difference between the warehouse mart and live mode?
- How is the deployment structured and why is it a single service?
- What does Gunicorn and Uvicorn do?
- How does the background scheduler work?

---

## 2. Umsa

**Role Title:** Frontend Dashboard, Visual Analytics, and User Experience Lead

**Main Responsibility:**
Umsa owns the dashboard experience and all visual analytics modules. She should explain how users interact with the project and how intelligence is presented visually.

### Work Areas

- Worked on the Next.js dashboard structure and component layout.
- Organized the drawer navigation and all dashboard sections.
- Worked on the visual presentation of:
  - Overview (KPI cards, mart health, intelligence feed)
  - Topic IQ (live search interface, brief cards, save brief, saved history)
  - Events (event timeline, cards, detail view)
  - Entities (entity cards with timeline)
  - Sentiment (pie/distribution chart, timeline chart)
  - Replay (narrative replay slider mode)
  - Compare (two-narrative comparison with delta metrics)
  - Graph (interactive knowledge graph with zoom, pan, fit view, focus, expansion)
  - Predictions (forecast cards per narrative)
  - Reports (PDF export, HTML view, CSV export)
  - Data Quality (quality profiling table per dataset)
  - Administration (ETL, warehouse, enrichment, ingestion, dataset upload)
- Built the filter/search bar that filters events, narratives, entities, and predictions.
- Improved responsiveness for laptop and exhibition-screen layouts.
- Worked on the branded footer with developer social links.
- Implemented the NarrativeIQ logo and branding in the header and footer.
- Helped implement all chart interactions (Recharts-based timelines, pie charts, bar charts).

### Modules Umsa Should Explain

- Dashboard overview and KPI cards.
- Drawer navigation and mobile/laptop responsive behavior.
- Topic IQ live search interface and what each metric card shows.
- Narrative Replay mode and how frames advance.
- Narrative Comparison Engine and how delta metrics work.
- Knowledge Graph Explorer and its interactive controls.
- Reports UI and how export buttons work.
- Filter search bar behavior.
- The color coding of lifecycle stages (Emerging, Growing, Peak, Declining, Archived).

### Key Files Umsa Should Know

- `frontend/src/components/DashboardApp.tsx` — Entire dashboard UI
- `frontend/src/app/globals.css` — Design system and all styling
- `frontend/src/components/Logo.tsx` — NarrativeIQ logo component
- `frontend/src/types/intelligence.ts` — TypeScript interfaces
- `frontend/src/data/narrativeiq_mart.json` — Bundled fallback mart data
- `frontend/next.config.ts` — Next.js configuration (static export mode)
- `frontend/package.json` — Frontend dependencies

### Exhibition Talking Points

- "The dashboard is not dummy UI. It connects to FastAPI at runtime. If the API fails, it falls back to the bundled mart so it never shows a blank screen."
- "The graph supports zoom, pan, fit-view, focus on selected node, and neighborhood expansion for deep relationship exploration."
- "Every chart is backed by real ETL-generated warehouse data or live public-source metadata."
- "The filter bar searches across all four data types simultaneously: events, narratives, entities, and predictions."

### Likely Viva Questions Umsa Can Answer

- How does the user navigate the dashboard?
- What happens when a user types in the search/filter bar?
- What is the purpose of the knowledge graph?
- How does narrative comparison work visually?
- How does Replay Mode work?
- How does the dashboard handle both warehouse data and live mode?
- How are reports exported?

---

## 3. Zilehuma

**Role Title:** Documentation, Reporting, Topic IQ Explanation, and Exhibition Presentation Lead

**Main Responsibility:**
Zilehuma owns documentation, the project proposal, exhibition storytelling, and explaining Topic IQ behavior clearly to evaluators.

### Work Areas

- Prepared and maintained project documentation files.
- Helped explain the project proposal and problem statement.
- Organized the demo flow for judges and evaluators.
- Focused on explaining Topic IQ:
  - How live sources are fetched (Wikipedia, GDELT, Google News)
  - How confidence, influence, strength, sentiment, and stage are calculated
  - How the "Save Brief" feature saves to PostgreSQL
  - How saved briefs appear in the "Saved Briefs History" section
- Explained the report generation pipeline:
  - HTML report (branded exhibition format)
  - PDF export (via Python report generator)
  - CSV summary export
- Documented future scope and how the current build compares to full production.
- Helped explain the NarrativeIQ logo, branding, and footer social links.
- Prepared answers for what is implemented and what is future work.

### Modules Zilehuma Should Explain

- Project description and problem statement.
- Topic IQ live search and what each intelligence metric means.
- Report generation (HTML, PDF, CSV).
- Current build status (fully live in production).
- Future scope (scheduled full ingestion, LLM enrichment, authentication).
- Demo flow: which order to present modules.

### Key Files Zilehuma Should Know

- `README.md` — Project overview
- `docs/EXHIBITION_DEMO_FLOW.md` — Demo flow guide
- `docs/FINAL_COMPLETION_AUDIT.md` — Completion status
- `docs/submission_2026_06_09/PROJECT_PROPOSAL.md` — Project proposal
- `docs/submission_2026_06_09/EXHIBITION_VS_FINAL_COMPARISON.md` — Version comparison
- `reports/generated/` — Generated HTML and PDF reports

### Exhibition Talking Points

- "NarrativeIQ is not just a trend counter. It explains why a topic matters, how it is evolving, and what may happen next."
- "Topic IQ is the live intelligence engine. It pulls from Wikipedia, GDELT, and Google News in real-time and produces a structured intelligence brief."
- "Every brief searched in Topic IQ is automatically saved to Supabase PostgreSQL so we have a persistent narrative intelligence history."
- "The project is fully deployed and live on Render. This is not a local demo — it is a production deployment."

### Likely Viva Questions Zilehuma Can Answer

- What problem does NarrativeIQ solve?
- What are the main features of NarrativeIQ?
- What external APIs and sources does Topic IQ use?
- How is the project useful in the real world?
- What does the confidence score mean?
- What is future planned work?

---

## 4. Laiqa

**Role Title:** ETL, Dataset, Data Quality, and Warehouse Concepts Lead

**Main Responsibility:**
Laiqa owns the data preparation and DW&BD explanation. She should explain how the data is generated, transformed, stored, and validated.

### Work Areas

- Studied and documented the 50,000-record generated exhibition dataset.
- Mapped project data into event, topic, entity, sentiment, and source structures.
- Explained all ETL pipeline stages (Extract → Transform → Load).
- Explained dimension and fact table design in the star schema.
- Explained how the data quality dashboard checks completeness, uniqueness, consistency, and timeliness.
- Explained why deterministic data (fixed seed) is used for exhibition stability.
- Prepared explanations for:
  - Synthetic generated data (warehouse base)
  - Live public-source metadata (Topic IQ)
  - Saved PostgreSQL snapshots (Topic briefs)
  - Mart aggregation (JSON dashboard output)
- Explained materialized views and why they exist.
- Explained the difference between warehouse data and mart data.

### Modules Laiqa Should Explain

- ETL pipeline stages and what each produces.
- The 4 events, 17 topics, and their entity configurations.
- All 6 dimension tables and 6 fact tables.
- The 4 materialized views and their SQL purpose.
- Data quality metrics (completeness, uniqueness, consistency, timeliness, quality score).
- The mart aggregation process and how it produces the dashboard JSON.
- What "Historical Through: 2026-06-01" means.
- Why the random seed is fixed at 130.

### Key Files Laiqa Should Know

- `etl/pipeline.py` — Complete ETL pipeline with all transformations
- `datasets/warehouse/` — All generated warehouse CSV files
- `datasets/marts/narrativeiq_mart.json` — Dashboard mart output
- `warehouse/001_schema.sql` — Star schema DDL
- `warehouse/002_materialized_views.sql` — Materialized view definitions
- `warehouse/003_live_topic_schema.sql` — Live Topic schema
- `docs/DWBD_CONCEPTS.md` — DW&BD concepts explanation
- `docs/submission_2026_06_09/DWBD_CONCEPTS_GUIDE.md` — Detailed concepts guide

### Exhibition Talking Points

- "ETL is the backbone. Without it, there is no data, no warehouse, and no dashboard."
- "We use a star schema with 6 dimension tables and 6 fact tables. This is exactly how a real data warehouse is designed."
- "Data quality is not just a label. We calculate completeness, uniqueness, consistency, and timeliness for every warehouse table."
- "The mart is a pre-aggregated analytical snapshot derived from warehouse facts and dimensions. It makes the dashboard fast without running SQL queries on every page load."
- "The pipeline is deterministic — running it with the same seed always produces the same data. This is essential for exhibition reliability."

### Likely Viva Questions Laiqa Can Answer

- What is ETL?
- What are fact tables and what do they store in this project?
- What are dimension tables and what do they store?
- Why did we use a star schema?
- What does data quality mean in this project?
- What is the difference between warehouse data and mart data?
- What does "Historical Through: 2026-06-01" mean?
- Why use deterministic (fixed-seed) data for the exhibition?

---

## Recommended Presentation Flow

1. **Zilehuma** introduces the project, problem statement, real-world purpose, and demo flow.
2. **Khalid** explains the architecture, warehouse schema, backend, PostgreSQL, and deployment.
3. **Laiqa** explains ETL, generated dataset, dimension/fact tables, data quality, and mart aggregation.
4. **Umsa** demonstrates the live dashboard, all modules, graph, replay, comparison, and reports.
5. **Khalid** closes with current production status, live deployment URL, and technical achievements.

---

## Important Coordination Notes

- Khalid should be ready for deep technical questions about architecture, database, and deployment.
- Umsa should be confident operating the live dashboard at the production URL.
- Zilehuma should be ready to explain the project motivation and Topic IQ intelligence metrics clearly.
- Laiqa should be ready to explain DW&BD concepts with simple examples from the actual codebase.
- **All members** must know the difference between deterministic warehouse data and live Topic IQ metadata.
- **All members** must know the production URL: https://narrativeiq-global-event-narrative.onrender.com/
- **All members** should say: "The dashboard is powered by ETL-generated mart data served through FastAPI. Topic IQ adds real live intelligence from Wikipedia, GDELT, and Google News RSS, and every brief is saved to Supabase PostgreSQL."
- **Never say** the dashboard is dummy UI. It is a production-deployed, fully functional system.
