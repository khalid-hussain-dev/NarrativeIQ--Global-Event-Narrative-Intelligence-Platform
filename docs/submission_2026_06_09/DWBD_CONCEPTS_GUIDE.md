# NarrativeIQ DW&BD Concepts Guide

Date: 2026-06-08

This document explains the Data Warehousing and Big Data concepts used in NarrativeIQ, why they were chosen, and how they work inside the project.

## 1. Warehouse-First Development

Meaning:

Warehouse-first development means the project is built around the data warehouse before building the final dashboard.

Why chosen:

The project is for Data Warehousing and Big Data, so the main focus must be structured data processing, storage, and analytics rather than only frontend screens.

Role in NarrativeIQ:

NarrativeIQ first generates and transforms data through ETL, then stores it in warehouse-style outputs, then exposes dashboard marts and APIs.

How it works:

1. `etl/pipeline.py` generates and transforms records.
2. Warehouse CSV files are written to `datasets/warehouse/`.
3. PostgreSQL schema is defined in `warehouse/001_schema.sql`.
4. The loader `etl/load_postgres.py` loads warehouse outputs.
5. Materialized views and marts support the dashboard.

Completion:

Implemented.

## 2. Big Data Simulation

Meaning:

Big Data usually means high volume, variety, velocity, and analytical complexity. In an academic lab project, a controlled large dataset can be used to demonstrate these ideas.

Why chosen:

Live collection from many sources can be unstable during exhibition. A deterministic dataset gives reliable results while still showing warehouse and analytics concepts.

Role in NarrativeIQ:

The dashboard uses 50,000 generated content records across events, topics, entities, sources, and sentiment values.

Completion:

Implemented for exhibition. Full production would use larger real historical and live datasets.

## 3. ETL Pipeline

Meaning:

ETL means Extract, Transform, Load.

Why chosen:

Raw data cannot directly support analytics. It must be collected, cleaned, standardized, scored, and loaded into a warehouse.

Role in NarrativeIQ:

ETL is the core engine that converts event and narrative signals into warehouse-ready data.

How it works:

- Extract: generate or collect event/topic/source/entity records.
- Transform: calculate sentiment, narrative strength, influence, growth, lifecycle stage, trend score, and quality metrics.
- Load: write warehouse CSV files and load them into PostgreSQL.

Completion:

Implemented through `etl/pipeline.py` and `etl/load_postgres.py`.

## 4. Data Cleaning And Transformation

Meaning:

Cleaning removes inconsistency. Transformation converts raw data into a structured analytical format.

Why chosen:

Narrative intelligence needs consistent dates, topics, event IDs, sentiment labels, entity references, and numeric scores.

Role in NarrativeIQ:

The pipeline normalizes data into keys and measures.

Examples:

- Dates become `date_key`.
- Sources become `source_key`.
- Topics become `topic_key`.
- Entities become `entity_key`.
- Sentiment labels become `sentiment_key`.
- Strength, growth, influence, and momentum are calculated.

Completion:

Implemented.

## 5. Star Schema

Meaning:

A star schema is a warehouse design where fact tables store measurements and dimension tables store descriptive context.

Why chosen:

It is simple, fast for analytics, and easy to explain in a DW&BD exhibition.

Role in NarrativeIQ:

NarrativeIQ uses dimensions for context and facts for measurable activity.

Example:

`fact_narrative` stores narrative strength and influence. It links to dimension tables such as date, event, and topic.

Completion:

Implemented.

## 6. Dimension Tables

Meaning:

Dimension tables describe the data. They answer questions like who, what, when, where, and which category.

Why chosen:

They avoid repeated descriptive values inside fact tables and make analytics easier.

Role in NarrativeIQ:

Important dimensions include:

- `dim_date`: time context.
- `dim_source`: source/platform context.
- `dim_event`: event cluster context.
- `dim_topic`: narrative topic context.
- `dim_entity`: people, organizations, products, groups, and locations.
- `dim_sentiment`: positive, neutral, and negative labels.
- `dim_live_topic`: saved arbitrary Topic IQ searches.

Completion:

Implemented.

## 7. Fact Tables

Meaning:

Fact tables store measurable data.

Why chosen:

The dashboard needs numeric measures such as engagement, mentions, strength, influence, sentiment, and growth.

Role in NarrativeIQ:

Important facts include:

- `fact_content`: content activity, engagement, reach, and popularity.
- `fact_narrative`: narrative strength, growth, influence, and lifecycle.
- `fact_sentiment`: sentiment scores over time.
- `fact_entity_mentions`: entity mention count and strength.
- `fact_trends`: trend score, growth rate, and momentum.
- `fact_live_topic_snapshot`: saved Topic IQ measurements.

Completion:

Implemented.

## 8. Historical Snapshots

Meaning:

Historical snapshots store measurements at different times so trends can be studied.

Why chosen:

NarrativeIQ is about evolution over time, not only current totals.

Role in NarrativeIQ:

Snapshots support:

- sentiment timelines
- narrative replay
- trend growth
- saved Topic IQ history
- lifecycle analysis

Completion:

Implemented for generated mart and saved live-topic snapshots.

## 9. Materialized Views

Meaning:

A materialized view stores the result of a query so analytics can load faster.

Why chosen:

Dashboards need fast aggregated results. Recalculating everything from raw facts every time is inefficient.

Role in NarrativeIQ:

Implemented views include:

- `mv_narrative_overview`
- `mv_sentiment_evolution`
- `mv_entity_influence`
- `mv_trend_velocity`

Completion:

Implemented.

## 10. Data Marts

Meaning:

A data mart is a smaller, purpose-specific analytical dataset prepared from the warehouse.

Why chosen:

The frontend should not directly calculate everything from raw warehouse tables.

Role in NarrativeIQ:

The generated mart powers dashboard modules such as overview, events, narratives, sentiment, graph, replay, predictions, and reports.

Completion:

Implemented through `datasets/marts/narrativeiq_mart.json`.

## 11. Data Quality Profiling

Meaning:

Data quality profiling checks whether data is complete, unique, consistent, and timely.

Why chosen:

A data warehouse must be trusted. Quality metrics help prove that the ETL output is reliable.

Role in NarrativeIQ:

The ETL pipeline creates quality rows for datasets and the dashboard displays quality scores.

Completion:

Implemented.

## 12. PostgreSQL Data Warehouse

Meaning:

PostgreSQL is used as the relational warehouse database.

Why chosen:

It supports relational schema design, SQL analytics, indexes, views, and reliable local deployment.

Role in NarrativeIQ:

PostgreSQL stores dimension tables, fact tables, live topic snapshots, and source rows.

Completion:

Implemented and locally configured.

## 13. Live Topic Ingestion

Meaning:

Live ingestion means collecting current public-source signals instead of relying only on stored data.

Why chosen:

The original project idea included searching for any topic and generating an intelligence brief.

Role in NarrativeIQ:

Topic IQ uses public metadata from:

- Wikipedia
- GDELT
- Google News RSS

It calculates confidence, signal counts, source clusters, sentiment, strength, and influence.

Completion:

Implemented as on-demand lightweight ingestion. Scheduled ingestion is still future work.

## 14. Knowledge Graph

Meaning:

A knowledge graph shows relationships between entities, topics, and narratives.

Why chosen:

Narratives do not exist alone. They involve people, organizations, products, groups, and related topics.

Role in NarrativeIQ:

The graph shows relationship types and strengths. The current dashboard supports zoom, pan, fit view, selected-node focus, and neighborhood expansion.

Completion:

Implemented for the current mart. Deeper backend-driven graph expansion is future work.

## 15. Narrative Replay

Meaning:

Replay shows how a narrative changes over time.

Why chosen:

NarrativeIQ is focused on lifecycle, not only static reporting.

Role in NarrativeIQ:

Replay mode shows monthly changes in dominant narratives, stage, sentiment, and strength.

Completion:

Implemented.

## 16. Narrative Comparison

Meaning:

Narrative comparison compares two narratives side by side.

Why chosen:

Analysts need to know which narrative is stronger, faster-growing, more influential, or more positive/negative.

Role in NarrativeIQ:

The comparison engine compares strength, growth, influence, sentiment, and monthly trajectory.

Completion:

Implemented.

## 17. Prediction Analytics

Meaning:

Prediction analytics estimate possible future movement.

Why chosen:

The project blueprint included forecast-style narrative intelligence.

Role in NarrativeIQ:

The prediction center shows expected growth direction, future strength, and confidence.

Completion:

Implemented at phase-1 heuristic level. More advanced ML/LLM prediction is future work.

## 18. Reporting

Meaning:

Reporting converts dashboard insights into shareable artifacts.

Why chosen:

Exhibitions and real analyst workflows need outputs that can be shown or submitted.

Role in NarrativeIQ:

The system generates:

- HTML report
- PDF report
- CSV summary

Completion:

Implemented.

## 19. Admin And Audit Logs

Meaning:

Admin controls manage ETL and warehouse operations. Audit logs record system actions.

Why chosen:

Warehouse systems need operational transparency.

Role in NarrativeIQ:

The admin panel shows ETL controls, warehouse load controls, PostgreSQL status, and recent audit events.

Completion:

Implemented for ETL, warehouse, report, and live-topic actions. Upload/import audit is future work.

## 20. End-To-End Working Flow

1. Event and narrative data is generated or collected.
2. ETL transforms it into clean warehouse structures.
3. Dimension and fact tables store context and measurements.
4. Materialized views and marts prepare fast analytical outputs.
5. FastAPI exposes the marts and admin operations.
6. Next.js dashboard visualizes intelligence modules.
7. Topic IQ adds on-demand live public-source context.
8. Saved Topic IQ briefs are persisted into PostgreSQL.
9. Reports export the final insights.
10. Audit logs record important system actions.

This is why NarrativeIQ qualifies as a Data Warehousing and Big Data project: it demonstrates volume, structured modeling, ETL, facts, dimensions, historical analysis, quality profiling, marts, APIs, dashboards, and analytical reporting.

