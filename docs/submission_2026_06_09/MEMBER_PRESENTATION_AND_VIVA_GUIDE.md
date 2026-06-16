# NarrativeIQ — Member Presentation and Viva Guide

**Date:** 2026-06-16 (Final Production Build)
**Live URL:** https://narrativeiq-global-event-narrative.onrender.com/
**Repository:** https://github.com/khalid-hussain-dev/NarrativeIQ--Global-Event-Narrative-Intelligence-Platform

This document gives each member a complete explanation script, implementation notes, module explanations, and viva answers. It covers every module, concept, metric, and API in the final production build of NarrativeIQ. Read this carefully. Every member should understand the entire system, even if they only present a part of it.

---

## Overall Project Opening (Any member can say this)

> "Our project is **NarrativeIQ** — a Global Event Narrative Intelligence Platform built on Data Warehousing and Big Data principles. It tracks how public narratives form, grow, compete, and influence people over time. The system uses an ETL pipeline, a PostgreSQL star-schema warehouse, precomputed materialized views, API-ready mart aggregates, a FastAPI backend, and an interactive Next.js dashboard. It includes live Topic IQ search, sentiment analytics, entity intelligence, narrative replay, comparison, prediction, knowledge graph, reports, data quality profiling, and an admin control panel. The entire system is deployed and live in production on Render."

---

## Recommended Presentation Order

1. Zilehuma — Project idea, problem statement, real-world use, demo flow.
2. Khalid — Architecture, backend, warehouse, PostgreSQL, deployment.
3. Laiqa — ETL, dataset, facts, dimensions, materialized views, data quality, marts.
4. Umsa — Live dashboard demo: overview, Topic IQ, replay, comparison, graph, predictions, reports, admin.
5. Khalid — Close with production status, live URL, technical achievements.

---

## Part 1: Khalid

### Role Summary

Khalid is the project lead and main technical integration owner. He explains the architecture, backend, warehouse, PostgreSQL, deployment, scheduler, and how everything connects.

### What Khalid Should Say

> "My role was to design and build the complete system architecture of NarrativeIQ. I took a warehouse-first approach — meaning the data pipeline, warehouse schema, and APIs were built before any dashboard card was shown. I worked on the ETL pipeline, the PostgreSQL star schema, the FastAPI backend, Topic IQ live ingestion with database saving, the DeepSeek AI enrichment pipeline, and the production deployment to Render as a single unified service."

### How the Architecture Works (Khalid's core explanation)

The system has four layers that flow top-to-bottom:

```
[ETL Pipeline]   →  [Warehouse CSVs + PostgreSQL]  →  [Mart JSON]  →  [FastAPI]  →  [Next.js Dashboard]
etl/pipeline.py      datasets/warehouse/*.csv           datasets/marts/    backend/     frontend/
                     PostgreSQL (Supabase)               *.json            app/main.py   src/
```

**Step 1 — ETL (Extract, Transform, Load):**
`etl/pipeline.py` generates 50,000 synthetic content records across 4 event clusters (AI Revolution, Cricket World Cup, Global Elections, Natural Disaster Response) and 17 topics. It applies lifecycle curves, sentiment biases, growth rates, and entity weights, then writes:
- Raw warehouse CSVs (`datasets/warehouse/`)
- Dimension and fact CSV files
- A mart JSON file (`datasets/marts/narrativeiq_mart.json`)

**Step 2 — PostgreSQL Warehouse:**
`etl/load_postgres.py` loads the warehouse CSVs into a PostgreSQL database (Supabase) with a proper star schema: 6 dimension tables and 6 fact tables. `warehouse/002_materialized_views.sql` creates 4 precomputed views for fast analytics.

**Step 3 — Mart JSON:**
The mart JSON is a denormalized, dashboard-ready aggregation of all warehouse data. It is cached in memory by `backend/app/services/mart_service.py` with a 30-second TTL so it refreshes automatically after ETL runs.

**Step 4 — FastAPI:**
`backend/app/main.py` exposes 30+ REST API endpoints. The frontend fetches `/dashboard`, `/events`, `/narratives`, `/entities`, `/sentiment`, `/graph`, `/predictions`, `/reports`, `/topic-intelligence`, and `/admin/*` endpoints.

**Step 5 — Next.js Dashboard:**
The frontend (`frontend/src/components/DashboardApp.tsx`) fetches data from FastAPI. If the API is unavailable, it falls back to the bundled mart JSON. In production, FastAPI also serves the static Next.js export files directly, so both the API and the UI come from the same Render service.

### Modules Khalid Should Explain

#### System Architecture (see diagram above)

#### PostgreSQL Warehouse

> "PostgreSQL is the relational database for our star-schema warehouse. We use Supabase, a cloud-hosted PostgreSQL service. The schema includes 6 dimension tables (dim_date, dim_source, dim_event, dim_topic, dim_entity, dim_sentiment) and 6 fact tables (fact_content, fact_narrative, fact_sentiment, fact_trends, fact_entity_mentions, entity_relationships). For live Topic IQ, we have 3 additional tables: dim_live_topic, fact_live_topic_snapshot, and live_topic_sources."

#### FastAPI Backend

> "FastAPI serves as the API layer between the warehouse/mart data and the dashboard. It exposes over 30 endpoints. All endpoints are documented at `/docs` (Swagger UI). The backend starts using Gunicorn with Uvicorn workers, which allows it to handle multiple concurrent requests efficiently in production."

#### Admin Panel

> "The admin panel proves operational control. From the UI, an authorized user can run ETL to regenerate 50,000 records, run the warehouse PostgreSQL loader, run DeepSeek enrichment on imported source packs, configure the live ingestion schedule, view the system audit log, and upload custom CSV datasets that get converted into named mart files."

#### Topic IQ PostgreSQL Saving

> "When a topic is searched in Topic IQ and live sources are found, the brief is automatically saved to Supabase. The topic name is upserted into dim_live_topic, a snapshot measurement is inserted into fact_live_topic_snapshot with all metrics, and each source article is saved to live_topic_sources. The Saved Briefs History section retrieves these using a JOIN SQL query."

#### Background Scheduler

> "The ingestion scheduler runs inside FastAPI as an asyncio background task. When enabled and given an interval (e.g., 60 minutes), it wakes up every interval, fetches all saved topic names from PostgreSQL, calls live_topic_profile() for each one, and saves the fresh snapshots back to PostgreSQL. This keeps your saved topics updated automatically without any manual action."

#### Unified Deployment

> "For production deployment, Next.js is built as a static export (npm run build with output: 'export'). FastAPI mounts this static export using StaticFiles at the root path. So when you visit the Render URL, FastAPI handles API requests at /health, /dashboard, /topic-intelligence, etc., and serves the React UI for all other paths. This means we need only one Render service for the full application."

### Khalid Viva Questions and Answers

**Q: What is the complete architecture?**
A: "NarrativeIQ follows a warehouse-first architecture. The ETL pipeline generates data, writes warehouse CSVs, and produces a mart JSON. The PostgreSQL loader imports the warehouse CSVs into a star schema with 6 dimension tables and 6 fact tables. Materialized views precompute analytics. FastAPI reads the mart JSON and exposes it through REST endpoints. The Next.js frontend fetches from FastAPI and visualizes the intelligence modules. In production, FastAPI also serves the static Next.js export, so only one service is needed."

**Q: Why PostgreSQL?**
A: "PostgreSQL is a proper relational database that supports schemas, fact and dimension tables, foreign keys, indexes, materialized views, and complex SQL queries. It makes the project a real data warehouse rather than just JSON files. It also enables Topic IQ snapshots to persist across sessions."

**Q: What is a materialized view?**
A: "A materialized view stores the result of a SQL query physically on disk. Instead of recalculating joins between fact_narrative, dim_event, and dim_topic on every request, mv_narrative_overview precomputes this join. This is a Data Warehousing optimization technique — trading storage for query speed."

**Q: What is Gunicorn and Uvicorn?**
A: "Uvicorn is an ASGI server that runs FastAPI. Gunicorn is a process manager that manages multiple Uvicorn worker processes. In production, Gunicorn ensures the app stays running and can handle multiple requests at once. We use the command: gunicorn -k uvicorn.workers.UvicornWorker app.main:app."

**Q: What is the difference between the warehouse mart and live mode?**
A: "The warehouse mart is a precomputed, stable JSON file generated from 50,000 deterministic records. Live mode calls live_topic_profile() which fetches real data from Wikipedia, GDELT, and Google News, computes intelligence metrics, and returns a mart-shaped response. Both use the same frontend format, so the dashboard renders identically for both modes."

---

## Part 2: Umsa

### Role Summary

Umsa owns the frontend dashboard and visual analytics. She demonstrates the live application and explains how each module is displayed and interacted with.

### What Umsa Should Say

> "My role was the dashboard experience and visual analytics. I worked on how users navigate the system, how each intelligence module is presented, and how the charts and interactive elements make the warehouse data understandable. The dashboard includes 14 modules accessible through a side drawer, all backed by real ETL-generated data and FastAPI endpoints."

### Modules Umsa Should Explain

#### Dashboard Overview

The Overview section shows:
- **Project identity and mart status** — which mart is loaded (e.g., "NarrativeIQ Warehouse (50K)"), mart generation time, and whether the backend API is online or offline.
- **KPI cards** — Total Records (50,000), Active Events (4), Active Narratives (17), Narrative Health Score, Warehouse Quality Score.
- **Intelligence Feed** — 3 auto-generated intelligence alerts from the mart data.
- **Dataset switcher** — A dropdown that lets users switch between uploaded named marts.
- **Bundled mart fallback** — If FastAPI is unreachable, the bundled mart JSON is loaded automatically.

> "The overview gives an executive-level picture of the entire warehouse state at a glance. The live API status indicator tells the presenter whether backend data is live or fallback."

#### Filter / Search Bar

A search input at the top right of the dashboard filters data across all modules simultaneously. When the user types:
- It tokenizes the query into lowercase words.
- It scores each event, narrative, entity, and prediction by how many query tokens match their name, category, region, or stage fields.
- Results with a score > 0 are shown; others are hidden.
- An orange "Filter active" badge appears showing how many results match.
- Clicking the X clears the filter.

> "The search bar is a cross-module filter. Typing 'AI' instantly narrows events to AI Revolution, narratives to AI topics, entities to OpenAI and GPT Models, and predictions to AI narratives — all at once."

#### Topic IQ — How It Works

Topic IQ is the live intelligence engine. When a user types any topic and clicks "Generate Brief":

1. The frontend sends a request to `GET /topic-intelligence/live-mart?q=<topic>` (or `/topic-intelligence?q=<topic>` for the brief-only view).
2. FastAPI calls `live_topic_profile(query)` in `topic_service.py`.
3. The function makes real HTTP calls to three external sources:
   - **Wikipedia API** — `en.wikipedia.org/api/rest_v1/page/summary/<title>` — gets article extract, word count, total search hits.
   - **GDELT Project API v2** — `api.gdeltproject.org/api/v2/doc/doc` — returns up to 20 news article references about the topic.
   - **Google News RSS** — `news.google.com/rss/search?q=<topic>` — returns up to 20 recent news headlines as XML, parsed into articles.
4. The function combines articles from GDELT and Google News, deduplicating by URL.
5. Metrics are calculated (see "How metrics are calculated" below).
6. The result is returned as a mart-shaped JSON and the dashboard renders it across all sections (Event, Narratives, Entities, Sentiment, Replay, Predictions, Graph).

If live sources return nothing, it falls back to `nearest_topic_profile()` which finds the best-matching event/narrative in the warehouse mart by tokenized string scoring.

#### How Topic IQ Metrics Are Calculated

| Metric | How It Is Calculated |
| --- | --- |
| **Influence** | `22 + source_weight + reference_weight * 0.55 + news_signals * 1.25 + popularity_weight` — grows with more sources, Wikipedia hits, and news coverage. Clamped 1–96. |
| **Total Signals** | `reference_signals + news_signals` — sum of Wikipedia-derived signals and news article relevance. |
| **Strength (Narrative Strength)** | `24 + reference_weight + news_weight + word_count_bonus + popularity_weight` — reflects how well-documented the topic is. Clamped 1–96. |
| **Sentiment** | Scans combined text (query + Wikipedia extract + article titles) for positive keywords (growth, launch, win, record) and negative keywords (ban, crisis, decline, scandal). Score = (pos - neg) / (pos + neg + 2). Label: Positive if > 0.12, Negative if < -0.12, else Neutral. |
| **Stage (Lifecycle)** | "Peak" if news_signals ≥ 15 or reference_signals ≥ 32. "Growing" if news_signals ≥ 5 or reference_signals ≥ 12. "Emerging" if any signals. "Reference" if only Wikipedia. |
| **Reference** | 1 (if Wikipedia exists) + min(40, total_hits // 25) + min(20, word_count // 180). Measures depth of encyclopedia coverage. |
| **News Signals** | `article_relevance * 0.62 + article_count * 0.35 + news_source_count * 1.15`. Measures breadth of current news coverage. |
| **Sources** | Count of unique news source domains + 1 (for Wikipedia). Represents the number of independent source clusters. |
| **Confidence** | Composite formula using 6 exponential saturation terms: reference signals, news signals, source count, relevance density, Wikipedia word count, and recent article count. Range: 35–96%. |

#### How the Graph Is Formed (Topic IQ / Live Mode)

1. Top 10 entities extracted from live articles and Wikipedia are placed as nodes.
2. A central "Topic" node is placed for the searched query.
3. Links are drawn from the topic node to each entity node.
4. Node size = mention strength score.
5. Link thickness = mention strength / 100.

In warehouse mode, graph nodes come from the top 16 entities and top 8 narratives in the mart. Links come from the pre-defined `RELATIONSHIPS` list in `pipeline.py` (e.g., OpenAI → GPT Models: CREATED, OpenAI → Microsoft: PARTNERSHIP).

#### How Related Narratives and Influence Entities Are Suggested

- **Related Narratives:** In warehouse mode, narratives that share the same `event_id` as the best-matching narrative are shown as related. In live mode, the 3 generated narratives are always Public Attention, Background Context, and Media Coverage — all variants of the same topic at different strength scales (100%, 72%, 52%).
- **Influence Entities:** In warehouse mode, entities are sorted by `latestMentions` and `mentionStrength` descending. In live mode, entities are extracted from all article titles and domain names using regex capitalized-word matching, ranked by mention frequency.

#### How KPI Metrics Are Calculated (Warehouse Mode)

| Metric | Calculation |
| --- | --- |
| **Raw Content Records** | Total number of rows in `fact_content` = total generated raw content items (50,000 by default). |
| **Active Events** | Hardcoded to `len(EVENTS)` = 4 (AI Revolution, Cricket World Cup, Global Elections, Natural Disaster Response). |
| **Active Narratives** | Total unique (event_id, topic) combinations in narrative rows = 17 narratives across 4 events. |
| **Narrative Health** | Average of (narrativeStrength + influenceScore) for all 4 events divided by 2 — clamped 1–100. |
| **Warehouse Quality** | Average of all per-dataset quality scores from the data quality profiling step. |

In live mode, these values come from the live profile: total_signals = totalRecords, active events = 1, active narratives = 3, health = narrativeStrength, quality = confidence.

#### Event Monitor

The Event Monitor is accessed via "Open Event Monitor" on the overview card. It opens a fullscreen view of all 4 events showing:
- Event name, category, region
- Narrative strength bar
- Growth rate
- Influence score
- Sentiment label and score
- Lifecycle stage badge

It is essentially a larger, more detailed version of the event cards, designed for exhibition presentation where the presenter wants to highlight a single event at a time.

#### Sentiment Mix — How Sentiments Are Calculated

**In Warehouse Mode (ETL-generated):**
For each topic/month row, the pipeline calculates:
```python
pos_share = clamp(0.36 + sentiment_score * 0.34, 0.10, 0.78)
neg_share = clamp(0.25 - sentiment_score * 0.22, 0.08, 0.62)
neutral_share = 1 - pos_share - neg_share
```
The raw volume is split into positive, neutral, and negative counts proportionally. These are summed across all latest-month rows for the overview distribution. The timeline shows monthly aggregates.

**In Live Mode (Topic IQ):**
Sentiment score is computed from keyword matching across the query, Wikipedia extract, and article titles. Then:
```python
positive_share = clamp(0.34 + sentiment_score * 0.28, 0.12, 0.72)
negative_share = clamp(0.24 - sentiment_score * 0.22, 0.08, 0.58)
neutral_share = 1 - positive_share - negative_share
```
The total sentiment volume = max(120, news_signals * 14 + reference_signals * 4 + 120).

#### Flagship Narrative Evolution (Replay Mode)

Replay Mode shows how narratives evolved over time, one month at a time:
- In warehouse mode: The AI Revolution event's monthly narrative data is pre-extracted into replay frames. Each frame contains the dominant narrative (highest strength that month), its lifecycle stage, its strength and sentiment score, and the top 4 active narratives.
- In live mode: One frame per month in the topic's 12-month timeline is generated. Narrative strength and stage are derived from the live topic profile timeline.
- The user plays through frames using a slider/play button. As the frame advances, the dominant narrative, stage, and chart update.

#### Intelligence Feed

The Intelligence Feed shows 3 auto-generated alert-style cards:
- **High severity:** "[Top growing topic] is accelerating — X% month-over-month growth."
- **Medium severity:** "[Top entity] leads entity influence — N latest mentions, strength score Y."
- **Low severity:** "Data quality gate passed — ETL quality score Z%."

In live mode, the feed is generated from the live article sources, showing the top articles ranked by index (first 2 = High, next 3 = Medium, rest = Low).

#### Prediction Center

Predictions are a 4-step forward linear extrapolation:
- In warehouse mode: Takes the last 6 timeline points for each of the top 6 narratives, averages the growth rate from the last 4 points, and forecasts 4 months forward using: `next_strength = current_strength * (1 + avg_growth / 100 * 0.28)`. Confidence decreases by ~7% per step.
- In live mode: Takes the last 3 points of each of the 3 live narratives, extrapolates growth linearly for 6 months forward.

#### Knowledge Graph Explorer

The graph uses a force-directed layout (via Recharts + custom SVG) with:
- **Zoom** — scroll wheel or +/- buttons
- **Pan** — drag the canvas
- **Fit View** — auto-fit all nodes to screen
- **Focus** — click a node to center and highlight it and its direct neighbors; other nodes fade
- **Expand** — from a focused node, expand to show its neighborhood (neighbors of neighbors)
- Node color = type (Entity, Narrative, Topic, Organization, Person)
- Edge thickness = relationship strength score
- Edge label = relationship type (CREATED, PARTNERSHIP, INFLUENCED, ADOPTED_BY, etc.)

#### Top Entities

Entities are ranked by `latestMentions` descending, then `mentionStrength`. Each entity card shows:
- Name and type (Organization, Person, Group, Location, Product, Topic)
- Total mentions (all-time aggregate)
- Latest mentions (most recent period)
- Mention strength score (1–99)
- Associated event name
- Monthly mention timeline chart

#### Top Growing Topics

Sorted by `growthRate` descending from the latest warehouse snapshot. Shows:
- Topic name, event name
- Trend score (0.62 × narrative_strength + 0.38 × influence_score)
- Growth rate (% month-over-month change)
- Momentum (growth_rate × 0.45 + narrative_strength × 0.22)

#### Narrative Comparison Engine

The user selects two narratives from dropdowns. The dashboard shows:
- Two side-by-side narrative cards with all metrics
- **Delta metrics:** Strength difference, growth difference, influence difference, sentiment difference — with "A leads" / "B leads" / "Equal" labels
- A combined timeline chart showing both narratives' strength over time
- Interpretation: which narrative is stronger, faster-growing, and more influential

The comparison uses data already present in the mart's narrative array — no additional API call.

#### Narrative Replay Mode (detailed)

- Each replay frame has: date, label (YYYY-MM), dominant narrative, lifecycle stage, strength score, sentiment score, and a list of active narratives with their individual strengths.
- The slider advances one frame at a time or auto-plays.
- The stage badge changes color per lifecycle stage: Emerging (blue), Growing (green), Peak (yellow), Declining (orange), Archived (gray).
- The strength bar fills proportionally.
- In warehouse mode, replay covers January 2023 to June 2026 for the AI Revolution event cluster.

#### Whole Administration Panel

The admin panel has these sub-sections:

1. **ETL Controls** — Run the pipeline with configurable record count (default 50,000). Takes ~10–30 seconds. Regenerates all warehouse CSVs and the mart JSON. The mart cache is cleared so the next dashboard load picks up fresh data.
2. **Warehouse Loader** — Runs `etl/load_postgres.py` to bulk-load all warehouse CSVs into PostgreSQL. Supports dry-run mode to check without writing. Requires NARRATIVEIQ_DATABASE_URL to be configured.
3. **DeepSeek AI Enrichment** — For an imported source pack, calls the DeepSeek API (deepseek-chat model) to enrich the rows with LLM-generated sentiment, topic tags, and summaries. Requires DEEPSEEK_API_KEY. The enriched artifact is saved and used in the next ETL run.
4. **Ingestion Scheduler** — Configures the background asyncio scheduler. Set an interval (e.g., 60 minutes) and enable it. The scheduler wakes up every interval, fetches all saved topic names from PostgreSQL, calls live_topic_profile() for each, and saves fresh snapshots back to the database.
5. **Dataset Upload** — Upload a custom CSV file. The backend runs the CSV adapter which auto-detects column roles (entities, dates, sentiment, metrics) and produces a named mart JSON. The mart appears in the dataset switcher dropdown.
6. **Source Pack Import** — Define a named source pack with topic, type, and rows as JSON. This is how manually curated data enters the pipeline before the next ETL run.
7. **System Audit Log** — Reads from `logs/admin_audit.jsonl`. Every admin action (ETL run, warehouse load, enrichment, schedule update, topic save, report export) is written here with timestamp, action, status, and details.
8. **Admin Status** — Shows mart metadata, warehouse file list and sizes, PostgreSQL configured status, and quality score.

All admin endpoints require the `X-Admin-Key` HTTP header to match the `NARRATIVEIQ_ADMIN_KEY` environment variable.

#### DeepSeek Enrichment

DeepSeek is an AI language model API. The enrichment pipeline:
1. Reads a source pack JSON from `datasets/imports/<importId>.json`.
2. Calls `etl/deepseek_enrichment.py` which sends each row to the DeepSeek API.
3. DeepSeek enriches each row with AI-generated sentiment labels, topic classifications, and summaries.
4. The enriched artifact is saved to `datasets/enriched/<importId>.json`.
5. On the next ETL run, the pipeline checks if an enriched version exists and uses it instead of the raw import.

This workflow allows real human-curated or scraped data to be AI-enriched before it enters the warehouse.

### Umsa Viva Questions and Answers

**Q: How does the user navigate the system?**
A: "The left side drawer contains all 14 modules. The user clicks a module name to jump to that section. The header also contains the mart status indicator, the dataset switcher dropdown, and the top-right search/filter bar."

**Q: What happens when a topic is searched in Topic IQ?**
A: "The query is sent to the FastAPI `/topic-intelligence/live-mart` endpoint. The backend calls `live_topic_profile()` which fetches from Wikipedia, GDELT, and Google News. Intelligence metrics are calculated, entities are extracted, and the result is returned as a full mart-compatible JSON. The dashboard re-renders all modules (events, narratives, entities, sentiment, replay, predictions, graph) with the live data. The brief is automatically saved to Supabase PostgreSQL."

**Q: What is the purpose of the knowledge graph?**
A: "The graph makes entity relationships visible. Instead of just listing entities, the graph shows who created what, who partnered with whom, who influences what topic, and which groups adopted which technology. This gives the presenter a visual way to explain influence pathways."

**Q: How does narrative comparison work?**
A: "Two narratives are selected from dropdowns. The system compares them across strength, growth rate, influence, and sentiment. Delta badges show which narrative leads on each metric. A combined timeline chart shows how both evolved over the same time period."

**Q: How does the dashboard handle API failures?**
A: "The dashboard first tries to fetch from FastAPI. If the request fails, it falls back to the bundled mart JSON that is embedded in the Next.js build. This means the dashboard always shows data, even if the backend is temporarily down."

**Q: How does the filter/search bar work?**
A: "The search bar tokenizes the query into lowercase words. For each event, narrative, entity, and prediction, it calculates a text relevance score by counting how many query tokens match the item's text fields. Items with score > 0 pass the filter. All modules update simultaneously with the filtered view."

---

## Part 3: Zilehuma

### Role Summary

Zilehuma owns documentation, project proposal explanation, exhibition storytelling, and Topic IQ explanation for evaluators.

### What Zilehuma Should Say

> "NarrativeIQ is a Data Warehousing and Big Data platform for narrative intelligence. Most trend dashboards tell you what is popular. NarrativeIQ tells you *why* a topic matters, *how* its narrative is evolving, *which* entities are driving it, *what* sentiment surrounds it, and *where* it is headed next. This system is fully live in production today."

### Modules Zilehuma Should Explain

#### Problem Statement

> "The problem is that organizations — from newsrooms to policy teams — have no structured system to understand how public narratives form, grow, compete, and fade over time. Raw social data is noisy. NarrativeIQ converts this noise into structured intelligence using ETL, warehouse architecture, and live source enrichment."

#### Topic IQ Live Search — External Sources

Topic IQ queries three external public APIs every time a topic is searched:

1. **Wikipedia MediaWiki API** (`en.wikipedia.org/w/api.php`)
   - Searches for the topic and retrieves the top article.
   - Fetches the article summary via the REST Summary API.
   - Provides: title, extract text, word count, total search hits, page URL, timestamp.
   - Used for: reference_signals, word_count_bonus, confidence.

2. **GDELT Project API v2** (`api.gdeltproject.org/api/v2/doc/doc`)
   - Queries GDELT's global media monitoring database for news articles about the topic.
   - Returns up to 20 article references including title, URL, domain, country, date.
   - Used for: news_signals, article_relevance, article_count.

3. **Google News RSS** (`news.google.com/rss/search`)
   - Parses the Google News RSS feed for the topic.
   - Returns up to 20 headlines with source name and publication date.
   - Used for: additional articles, source_count, recent article detection.

> "NarrativeIQ does not store or scrape full article content. It uses only publicly available metadata — titles, domains, dates — which is both ethical and lightweight."

#### Report Generation

- **HTML Report** — Generated by `reports/generate_report.py`. Produces a branded, styled HTML file with the mart data visualized as tables and summaries.
- **PDF Report** — Generated by `reports/export_report_pdf.py` using `weasyprint`. Converts the HTML report to a PDF file for sharing.
- **CSV Export** — The frontend directly downloads a summary CSV from the mart's `reportSummary` fields without any backend call.
- The API endpoint `POST /reports/export/pdf` triggers both generation steps and returns a download URL.

#### What "Historical Through: 2026-06-01" Means

The ETL pipeline generates data for all months from January 2023 to June 2026. "Historical Through: 2026-06-01" is the `latest_date` value found in the generated narrative rows — the most recent month for which warehouse data exists. It appears in the mart as `historicalThrough` and is shown in the dashboard sidebar as the data freshness indicator.

> "It means our warehouse contains narrative intelligence data covering January 2023 through June 2026. This is the temporal coverage of our exhibition dataset."

### Zilehuma Viva Questions and Answers

**Q: What problem does NarrativeIQ solve?**
A: "It solves the problem of understanding public narratives beyond simple trend counts. It shows how narratives emerge, peak, and decline; which entities drive them; how sentiment shifts over time; and what the most likely near-term trajectory is."

**Q: What external APIs does Topic IQ use?**
A: "Topic IQ uses three public APIs: the Wikipedia MediaWiki API for reference depth and word count, the GDELT Project API v2 for global news article metadata, and the Google News RSS feed for recent headlines. All three are free and publicly accessible."

**Q: What does the confidence score mean in Topic IQ?**
A: "Confidence represents how much evidence NarrativeIQ found for this topic across all sources. It is calculated from 6 factors using exponential saturation: reference signals, news signals, source count, query relevance density, Wikipedia word count, and recency of articles. A topic with a Wikipedia article, many GDELT results, and recent Google News coverage will have high confidence (80–96%). An obscure topic with minimal sources will have low confidence (35–50%)."

**Q: Is the project live in production?**
A: "Yes. The project is deployed at https://narrativeiq-global-event-narrative.onrender.com/ using Render, with Supabase PostgreSQL as the cloud database."

---

## Part 4: Laiqa

### Role Summary

Laiqa owns the ETL, dataset, data quality, and DW&BD explanation. She explains how the data is structured, transformed, and validated.

### What Laiqa Should Say

> "In NarrativeIQ, the data does not start from the dashboard. It starts from the ETL pipeline. ETL produces structured warehouse tables. Those tables are loaded into PostgreSQL with a proper star schema. Materialized views precompute analytics. The mart aggregates everything into a dashboard-ready JSON. None of the dashboard values are hard-coded — they are all derived from this data pipeline."

### Modules Laiqa Should Explain

#### ETL Pipeline — Three Stages

**Extract:**
The pipeline does not read from external files for the warehouse base data. It generates 50,000 synthetic content records using a deterministic random seed (seed=130). The events and topic configurations are hard-coded in `pipeline.py` as Python dataclasses:
- 4 events: AI Revolution, Cricket World Cup, Global Elections, Natural Disaster Response
- Each event has 4–5 topics with lifecycle curve parameters
- Each event has 5–6 entity configurations with influence weights
- Random seed = 130 ensures the same 50,000 records every run

**Transform:**
For each topic/month combination:
- Lifecycle progress = (month_index - start_offset) / duration
- Lifecycle strength = sin(progress × π) — a bell curve peaking at midpoint
- Volume = amplitude × lifecycle_strength × seasonal_factor
- Growth rate = (volume - previous_volume) / previous_volume × 100
- Sentiment score = sentiment_bias + sin_drift + random noise (clamped ±0.72)
- Influence score = lifecycle_curve × 82 + |growth_rate| × 0.11 + noise
- Narrative strength = (volume / amplitude) × 100
- Lifecycle stage = Emerging → Growing → Peak → Declining → Archived based on progress thresholds

**Load:**
The pipeline writes:
- `datasets/raw/raw_content.csv` — 50,000 raw content records
- `datasets/warehouse/dim_*.csv` — 6 dimension CSVs
- `datasets/warehouse/fact_*.csv` — 6 fact CSVs
- `datasets/warehouse/data_quality_report.csv` — quality metrics
- `datasets/marts/narrativeiq_mart.json` — dashboard mart
- `frontend/public/data/narrativeiq_mart.json` — frontend static copy
- `etl/load_postgres.py` loads all CSVs into PostgreSQL

#### Star Schema Design

```
                    dim_date
                       |
dim_source ←→ fact_content ←→ dim_event
                       |
                    dim_topic
                       |
                 dim_sentiment

fact_narrative: topic_key + event_key + date_key → strength, growth, influence, stage
fact_sentiment: event_key + sentiment_key + date_key → score, polarity, content_count
fact_entity_mentions: entity_key + event_key + date_key → mention_count, mention_strength
fact_trends: topic_key + event_key + date_key → trend_score, growth_rate, momentum
entity_relationships: source_entity_key → target_entity_key → relationship_type, strength
```

#### Dimension Tables

| Table | Description | Key Fields |
| --- | --- | --- |
| `dim_date` | Calendar hierarchy | date_key, full_date, day, week, month, quarter, year |
| `dim_source` | Content source registry | source_key, source_id, source_name, source_type, platform |
| `dim_event` | Event clusters | event_key, event_id, event_name, category, region, start_date, end_date |
| `dim_topic` | Narrative topics | topic_key, topic_name, topic_category |
| `dim_entity` | People, orgs, groups, products | entity_key, entity_name, entity_type |
| `dim_sentiment` | Sentiment labels | sentiment_key, sentiment_label (Positive/Neutral/Negative) |

#### Fact Tables

| Table | Grain | Measures |
| --- | --- | --- |
| `fact_content` | One row per content item | engagement_score, reach_score, popularity_score |
| `fact_narrative` | One row per topic per month | narrative_strength, growth_rate, influence_score, lifecycle_stage |
| `fact_sentiment` | One row per event per sentiment per month | sentiment_score, polarity, content_count |
| `fact_trends` | One row per topic per month | trend_score, growth_rate, momentum |
| `fact_entity_mentions` | One row per entity per event per month | mention_count, mention_strength |
| `entity_relationships` | One row per entity pair | relationship_type, strength_score |

#### Materialized Views

| View | Purpose |
| --- | --- |
| `mv_narrative_overview` | Pre-joins fact_narrative + dim_event + dim_topic + dim_date for fast narrative queries |
| `mv_sentiment_evolution` | Pre-aggregates sentiment counts grouped by event + date + label |
| `mv_entity_influence` | Pre-aggregates total mentions and average strength per entity per event |
| `mv_trend_velocity` | Pre-joins fact_trends with topic, event, date for fast trend queries |

> "Materialized views are physical tables on disk that store precomputed query results. They make analytics dashboards faster by avoiding expensive JOIN recalculations on every request."

#### Data Quality Profiling

For every warehouse dataset, the pipeline calculates:

| Metric | Calculation |
| --- | --- |
| **Completeness** | `100 - (missing_values / total_fields × 100)`. Measures what % of fields are non-null and non-empty. |
| **Uniqueness** | `100 - (duplicate_rows / total_rows × 100)`. Measures what % of rows are unique. |
| **Consistency** | Fixed at 98.5% for generated data (represents format and type consistency). |
| **Timeliness** | Fixed at 97.8% for generated data (represents data currency). |
| **Quality Score** | Average of all four metrics. |

The overall warehouse quality score (shown on the dashboard) is the average quality score across all 13+ datasets.

#### What Is a Mart and How Is It Used

A **data mart** is a subject-specific, denormalized analytical dataset prepared from warehouse data. In NarrativeIQ:

1. The ETL pipeline calls `aggregate_mart()` after building all facts and dimensions.
2. This function aggregates the latest month's data for each event, groups narratives with their full timeline, ranks entities, builds the graph structure, generates predictions, creates replay frames, and computes the intelligence feed.
3. The result is a single JSON file (`narrativeiq_mart.json`) approximately 2–5MB in size.
4. FastAPI reads this JSON on each `/dashboard` request using a 30-second TTL in-memory cache.
5. The frontend can also load this file directly from `/public/data/` if the API is offline.

> "The mart is the bridge between the raw warehouse data and the dashboard. Without the mart aggregation step, the dashboard would need to run complex SQL every page load. The mart makes it fast, portable, and deployable without a database."

#### Why "Historical Through: 2026-06-01"

The ETL generates monthly data from `date(2023, 1, 1)` to `date(2026, 6, 1)` — exactly 42 months. The `historicalThrough` field in the mart is set to the maximum date found in the narrative rows, which is `2026-06-01`. This is displayed in the sidebar to tell users how recent the warehouse data is.

### Laiqa Viva Questions and Answers

**Q: What is ETL?**
A: "ETL stands for Extract, Transform, Load. In our project: Extract generates 50,000 raw content records deterministically. Transform calculates narrative strength, growth rates, sentiment scores, influence scores, and lifecycle stages. Load writes all results to warehouse CSVs, PostgreSQL tables, and the mart JSON."

**Q: What are fact tables?**
A: "Fact tables store measurable, numerical values. In NarrativeIQ: fact_content stores engagement, reach, and popularity per content item. fact_narrative stores narrative strength, growth, and influence per topic per month. fact_sentiment stores positive, neutral, and negative counts per event per month. fact_entity_mentions stores mention counts and strength per entity per month."

**Q: What are dimension tables?**
A: "Dimension tables store descriptive context for the facts. dim_date stores calendar hierarchy. dim_event stores event name, category, and region. dim_topic stores topic names and categories. dim_entity stores entity names and types. dim_source stores source names and platforms. dim_sentiment stores the three sentiment labels."

**Q: Why star schema?**
A: "Star schema puts the fact tables at the center and dimensions around them. It is simple to understand, fast for analytical queries, and standard in data warehouse design. Our schema looks exactly like a star — fact tables in the center surrounded by dimension tables."

**Q: What does data quality score mean?**
A: "It means we checked every warehouse output for completeness (no missing fields), uniqueness (no duplicate rows), consistency (proper format and types), and timeliness (up-to-date data). The overall quality score is the average across all 13 datasets. For our generated data, it is typically 98–99%."

**Q: What is the difference between warehouse data and mart data?**
A: "Warehouse data is the normalized base layer — facts and dimensions in separate tables, optimized for storage and SQL queries. Mart data is a denormalized analytical output — everything pre-joined, pre-aggregated, and packaged as a JSON file for fast dashboard consumption."

**Q: Why use deterministic generated data?**
A: "Using a fixed random seed (seed=130) means every ETL run produces exactly the same 50,000 records. This makes the exhibition stable and reproducible. A live data source could fail during a demo, but our warehouse never changes unless we intentionally re-run the pipeline with new parameters."

---

## Shared Viva Answers (All Members)

**Q: Is the project complete?**
A: "The project is fully functional and deployed in production. The core features — ETL, warehouse, PostgreSQL, FastAPI, dashboard, Topic IQ, live ingestion, admin panel, reports — are all complete and working. Future work would include full scheduled ingestion for all topics, a richer AI enrichment workflow, user authentication, and automated testing coverage."

**Q: What makes this a Data Warehousing and Big Data project?**
A: "It uses a 50,000-record dataset, a proper ETL pipeline, a star-schema warehouse with 6 dimension tables and 6 fact tables, PostgreSQL loading, 4 materialized views, data mart aggregation, data quality profiling, API-backed analytics, and an interactive intelligence dashboard. These are all core DW&BD concepts applied to a real-world narrative intelligence use case."

**Q: Is Topic IQ fully live or simulated?**
A: "Topic IQ performs real HTTP requests to Wikipedia, GDELT, and Google News every time a topic is searched. The results are real, live, public-source metadata. The only simulated part is the warehouse base data (50,000 generated records), which is intentionally deterministic for exhibition stability. The two layers complement each other: warehouse provides historical depth, Topic IQ provides live recency."

**Q: What should not be said?**
A: "Do not say the dashboard is only dummy UI. Say it is powered by an ETL-generated mart, served through FastAPI, with real live Topic IQ ingestion and Supabase PostgreSQL persistence. The system is not a mockup — it is a deployed production application."

**Q: What APIs are used in the project?**

External APIs:
| API | Purpose | Used In |
| --- | --- | --- |
| Wikipedia MediaWiki API | Reference depth, word count, article extract | Topic IQ |
| GDELT Project API v2 | Global news article metadata | Topic IQ |
| Google News RSS | Recent headlines and source metadata | Topic IQ |
| DeepSeek Chat API | AI enrichment of imported source packs | Admin Enrichment |
| Supabase PostgreSQL | Cloud-hosted relational warehouse | Topic saving, warehouse loading |

Internal FastAPI endpoints (selected):
| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/health` | GET | System health check |
| `/dashboard` | GET | Full mart JSON |
| `/events` | GET | Events array |
| `/narratives` | GET | All narratives |
| `/entities` | GET | All entities |
| `/sentiment` | GET | Sentiment distribution + timeline |
| `/predictions` | GET | Prediction forecasts |
| `/graph` | GET | Knowledge graph nodes + links |
| `/topic-intelligence` | GET | Topic IQ brief (warehouse fallback) |
| `/topic-intelligence/live-mart` | GET | Topic IQ full live mart |
| `/topic-intelligence/save` | POST | Save brief to PostgreSQL |
| `/topic-intelligence/saved` | GET | List saved briefs |
| `/admin/etl/run` | POST | Run ETL pipeline |
| `/admin/warehouse/load` | POST | Load warehouse to PostgreSQL |
| `/admin/enrichment/run` | POST | Run DeepSeek enrichment |
| `/admin/ingestion/schedule` | POST | Configure scheduler |
| `/admin/datasets/upload` | POST | Upload CSV dataset |
| `/reports/export/pdf` | POST | Generate PDF report |
| `/reports/download/pdf` | GET | Download PDF |
| `/api` | GET | API root info |
| `/docs` | GET | Swagger UI |

**Q: How do APIs connect with the system?**
A: "The frontend makes HTTP fetch() calls to the FastAPI backend using relative URLs (since frontend and backend are on the same Render service). FastAPI processes the request, reads from the mart JSON cache or PostgreSQL, and returns JSON. The frontend renders the response into the appropriate module. All API calls include the `X-Admin-Key` header for protected admin endpoints. CORS is configured for localhost:3000 in development and is not needed in production since both are the same origin."

**Q: How does PostgreSQL connect to the system?**
A: "The backend reads the `NARRATIVEIQ_DATABASE_URL` environment variable set in Render. This is the Supabase PostgreSQL connection string. The backend uses the `psql` command-line tool (through Python subprocess) to run SQL commands. For Topic IQ saving, it uses CTEs to upsert the topic into dim_live_topic and insert a snapshot into fact_live_topic_snapshot. For listing saved briefs, it runs a JOIN query between these tables and returns JSON using PostgreSQL's `json_agg` function."
