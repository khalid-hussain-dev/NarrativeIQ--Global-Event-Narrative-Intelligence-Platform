# NarrativeIQ Member Presentation And Viva Guide

Date: 2026-06-09

This document gives each member a clear explanation script, implementation explanation, module explanation, and likely viva answers. It is written so each member can speak confidently during the project exhibition.

Current role split:

| Member | Main Area | Scope |
| --- | --- | ---: |
| Khalid | Project lead, architecture, backend, warehouse, integration | 38% |
| Umsa | Frontend dashboard, visual analytics, user flow | 26% |
| Zilehuma | Documentation, reporting, Topic IQ explanation, exhibition story | 18% |
| Laiqa | ETL, dataset, data quality, warehouse concepts | 18% |

## Overall Project Opening

Any member can say this if asked for a short project introduction:

"Our project is NarrativeIQ, a Data Warehousing and Big Data platform for narrative intelligence. It analyzes how public narratives form, grow, compete, and influence people over time. The system uses an ETL pipeline, a star-schema warehouse, PostgreSQL loading, materialized views, API-ready marts, and an interactive dashboard. It includes Topic IQ search, sentiment analytics, entity intelligence, narrative replay, comparison, prediction, reports, data quality, and admin controls."

Important shared point:

"The dashboard is not only dummy UI. The main dashboard is powered by ETL-generated mart data, FastAPI endpoints, and warehouse-style CSV/PostgreSQL structures. Topic IQ also uses live public-source metadata and can save searched topic snapshots into PostgreSQL."

## Recommended Presentation Order

1. Zilehuma introduces the project idea, proposal, problem, features, and final vision.
2. Khalid explains the architecture, backend, warehouse, PostgreSQL, and integration.
3. Laiqa explains ETL, dataset, facts, dimensions, marts, and data quality.
4. Umsa demonstrates the dashboard, graph, replay, comparison, reports, and user flow.
5. Khalid closes with current completion, final scope, and technical strengths.

## Khalid

### Role Summary

Khalid is the project lead and main technical integration owner. His responsibility is to explain the complete system architecture and how the ETL, warehouse, backend, PostgreSQL, and frontend connect together.

### What Khalid Should Say

"My role was to lead the technical architecture and integration of NarrativeIQ. I focused on making sure the project followed a warehouse-first approach. That means we did not simply create dashboard cards. We first prepared the data flow, then designed warehouse tables, then exposed APIs, and finally connected everything to the dashboard."

"I worked mainly on the backend, warehouse connection, PostgreSQL configuration, API integration, admin controls, and final system flow. The goal was to make the project explainable as a real Data Warehousing and Big Data project."

### How Khalid's Work Was Implemented

Khalid's work can be explained in these steps:

1. Architecture planning:
   - Divided the project into ETL, warehouse, backend, frontend, reports, and documentation layers.
   - Ensured that the dashboard depends on generated mart data instead of hard-coded UI values.

2. Warehouse integration:
   - Used PostgreSQL as the main relational warehouse database.
   - Connected generated warehouse CSV files with the PostgreSQL loader.
   - Verified that the local database can store the generated warehouse facts and dimensions.

3. Backend API layer:
   - Used FastAPI to expose dashboard, event, narrative, entity, sentiment, graph, report, Topic IQ, and admin endpoints.
   - Added a friendly root API route and health route.
   - Connected frontend requests to backend data.

4. Admin controls:
   - Added controls for running ETL, checking the warehouse loader, loading warehouse data, and viewing system audit logs.
   - Added persistent audit logging so important system actions are recorded.

5. Live Topic IQ persistence:
   - Helped connect Topic IQ saved briefs to PostgreSQL.
   - Live searched topics are stored in `dim_live_topic`, `fact_live_topic_snapshot`, and `live_topic_sources`.

### Modules Khalid Should Explain

#### System Architecture

Say:

"The system has a layered architecture. The ETL layer prepares data, the warehouse layer stores structured facts and dimensions, FastAPI exposes the data, and the Next.js dashboard visualizes it."

Simple flow:

`ETL -> Warehouse CSVs -> PostgreSQL -> Materialized Views/Marts -> FastAPI -> Dashboard`

#### PostgreSQL Warehouse

Say:

"PostgreSQL is used because it supports relational warehouse design, SQL queries, fact tables, dimension tables, and materialized views. It makes the system more realistic than keeping everything only in frontend files."

#### FastAPI Backend

Say:

"FastAPI works as the bridge between the warehouse/mart data and the dashboard. It exposes endpoints for dashboard data, Topic IQ, reports, graph, predictions, ETL quality, and admin operations."

#### Admin Panel

Say:

"The admin panel is used to show operational control. It displays mart records, warehouse files, quality score, PostgreSQL status, ETL controls, warehouse loader controls, and system audit log."

#### Topic IQ PostgreSQL Saving

Say:

"When a topic brief is saved, it is not only shown in the UI. It is inserted into PostgreSQL as a live topic dimension and a snapshot fact. Its sources are also saved separately."

### Khalid Viva Questions And Answers

Question: What is the complete architecture of the project?

Answer:

"NarrativeIQ follows a warehouse-first architecture. The ETL pipeline generates and transforms data, warehouse CSV files are created, PostgreSQL stores facts and dimensions, materialized views prepare analytical summaries, FastAPI exposes APIs, and the Next.js dashboard visualizes the intelligence modules."

Question: Why did you use PostgreSQL?

Answer:

"PostgreSQL was used because this is a Data Warehousing project and we needed a relational database that supports schemas, SQL, fact tables, dimension tables, and materialized views. It also allows saved Topic IQ snapshots to persist beyond the UI."

Question: What is the difference between fact and dimension tables?

Answer:

"Dimension tables store descriptive context, such as date, event, source, topic, entity, and sentiment. Fact tables store measurable values, such as content count, sentiment score, narrative strength, influence score, entity mentions, and trend growth."

Question: How does Topic IQ save data?

Answer:

"Topic IQ generates a brief from public-source metadata. When the user clicks Save Brief, the topic is saved in `dim_live_topic`, the measurement is saved in `fact_live_topic_snapshot`, and the source details are saved in `live_topic_sources`."

Question: What is real and what is simulated?

Answer:

"The main dashboard mart uses deterministic generated data so the exhibition demo remains stable. Topic IQ uses lightweight live public-source metadata from Wikipedia, GDELT, and Google News RSS. PostgreSQL persistence for saved Topic IQ snapshots is real."

Question: Is the backend fully production-ready?

Answer:

"The backend is functional for exhibition and supports the required APIs. For a full production version, it should be further separated into routers, services, repositories, authentication, and deployment layers."

## Umsa

### Role Summary

Umsa owns the frontend dashboard, visual analytics, dashboard navigation, and user experience. Her responsibility is to demonstrate how a user interacts with NarrativeIQ and how the analysis is shown visually.

### What Umsa Should Say

"My role was to work on the dashboard experience and visual analytics. I focused on how users move through the system, how each module is displayed, and how the dashboard presents warehouse intelligence clearly."

"The dashboard includes overview, Topic IQ, events, entities, sentiment, replay, comparison, graph, predictions, reports, data quality, and administration. My focus was to make these modules easy to navigate and understandable during the exhibition."

### How Umsa's Work Was Implemented

Umsa's work can be explained in these steps:

1. Dashboard structure:
   - Organized all major modules into a single interactive dashboard.
   - Used a drawer menu so users can jump between sections.

2. User navigation:
   - Added hamburger drawer behavior.
   - Added scrollable navigation so all menu items remain visible.
   - Added search behavior so users can find events, entities, narratives, and predictions.

3. Visual analytics:
   - Used charts and panels to show narrative strength, sentiment, predictions, trend movement, and entity influence.
   - Kept the UI suitable for an intelligence dashboard.

4. Interactive modules:
   - Helped present narrative replay.
   - Helped present narrative comparison.
   - Helped improve the knowledge graph controls.

5. Reports and responsive flow:
   - Worked on the report action buttons.
   - Made sure the dashboard is usable on laptop and mobile screens.

### Modules Umsa Should Explain

#### Dashboard Overview

Say:

"The overview gives the first intelligence summary. It shows the project identity, mart status, generated data time, total records, active events, active narratives, and quality score."

#### Drawer Navigation

Say:

"The drawer menu is used to move between all modules. It keeps the dashboard organized and helps the presenter quickly jump to any section during the demo."

#### Topic IQ Interface

Say:

"Topic IQ allows the user to enter any topic. It generates a topic intelligence brief and shows confidence, influence, strength, sentiment, evidence metrics, related narratives, entities, and sources."

#### Narrative Replay

Say:

"Replay mode shows narrative evolution over time. It helps explain how a narrative moves through stages like emergence, growth, peak, decline, or mutation."

#### Narrative Comparison

Say:

"The comparison engine lets us choose two narratives and compare their strength, growth, influence, sentiment, and timeline. This helps identify which narrative is more powerful."

#### Knowledge Graph

Say:

"The knowledge graph shows relationships between entities and narratives. It supports zoom, pan, fit view, selected-node focus, and expansion of a node's direct neighborhood."

#### Reports UI

Say:

"The reports section allows exporting the project insights as PDF, opening the HTML report, or exporting a CSV summary."

### Umsa Viva Questions And Answers

Question: How does the user navigate the system?

Answer:

"The user uses the drawer menu to move between modules. The dashboard also has search behavior and section actions that jump directly to relevant modules like Graph, Reports, Replay, or Topic IQ."

Question: Is the dashboard dummy?

Answer:

"No, the dashboard is not only dummy UI. It loads data from FastAPI when the backend is running. If the backend is unavailable, it has a bundled mart fallback. The values come from ETL-generated mart data."

Question: What happens when a topic is searched?

Answer:

"The query is sent to the FastAPI Topic IQ endpoint. The backend collects lightweight public-source metadata, calculates confidence and intelligence metrics, and sends a brief back to the dashboard."

Question: What is the purpose of the graph?

Answer:

"The graph helps explain relationships between narratives, entities, organizations, groups, products, and people. It makes influence pathways easier to understand visually."

Question: How does narrative comparison work visually?

Answer:

"Two narratives are selected from dropdowns. The dashboard displays both narrative cards, delta metrics, and a timeline chart so we can compare their strength over time."

Question: How do reports get exported?

Answer:

"The Reports section calls backend report endpoints. PDF export generates a branded PDF, HTML opens the generated report, and CSV exports a summary from the current dashboard mart."

## Zilehuma

### Role Summary

Zilehuma owns documentation, project proposal explanation, Topic IQ explanation, report explanation, and exhibition storytelling. Her responsibility is to explain the purpose, value, features, current version, final version, and presentation flow.

### What Zilehuma Should Say

"My role was to prepare and explain the project documentation and exhibition story. I focused on making the project easy to understand for evaluators, especially the project proposal, the difference between exhibition and final version, Topic IQ behavior, reporting, and future scope."

"NarrativeIQ is not only a dashboard. It is a narrative intelligence platform that uses Data Warehousing and Big Data concepts to understand how public narratives evolve and influence people."

### How Zilehuma's Work Was Implemented

Zilehuma's work can be explained in these steps:

1. Project proposal:
   - Prepared the project title and description.
   - Explained the aim of NarrativeIQ clearly without making it too technical.

2. Exhibition story:
   - Organized the demo flow from project introduction to dashboard modules.
   - Prepared simple language for judges and viva.

3. Version comparison:
   - Documented the difference between Exhibition MVP and Full Final Project.
   - Clearly separated implemented features from pending features.

4. Topic IQ explanation:
   - Prepared explanation of how topic search works.
   - Explained confidence, source clusters, live metadata, and saved snapshots.

5. Reporting and branding:
   - Explained report exports in HTML, PDF, and CSV.
   - Explained where the logo is used in the project.

### Modules Zilehuma Should Explain

#### Project Description

Say:

"NarrativeIQ analyzes how public narratives form, grow, compete, and influence people. It uses ETL, a data warehouse, PostgreSQL, APIs, and dashboards to convert narrative signals into intelligence."

#### Problem Statement

Say:

"Normal trend dashboards only show what is popular. NarrativeIQ tries to explain why a topic is important, how it is evolving, which entities are involved, what sentiment is attached to it, and what may happen next."

#### Topic IQ Live Search

Say:

"Topic IQ lets us search any topic. The system uses public-source metadata and creates a brief with confidence, influence, strength, sentiment, evidence signals, related narratives, and sources."

#### Report Generation

Say:

"Reports convert the analysis into shareable outputs. The project supports branded HTML report, PDF export, and CSV summary."

#### Exhibition Version vs Final Version

Say:

"The exhibition version is complete and stable for demo. The final version would add scheduled ingestion, real source packs as primary input, DeepSeek/LLM enrichment, authentication, tests, and stronger deployment architecture."

#### Demo Flow

Say:

"The recommended demo flow is: overview, Topic IQ, save brief, live warehouse history, dashboard analytics, graph, reports, administration, and final explanation."

### Zilehuma Viva Questions And Answers

Question: What problem does NarrativeIQ solve?

Answer:

"It solves the problem of understanding public narratives beyond simple trend counts. It shows how narratives evolve, which entities influence them, how sentiment changes, and how narratives compare."

Question: What are the main features?

Answer:

"Main features include Topic IQ search, event analytics, sentiment analysis, entity intelligence, narrative replay, narrative comparison, knowledge graph, prediction center, reports, data quality, and admin controls."

Question: How is the project useful?

Answer:

"It can help analysts, students, researchers, media teams, and decision-makers understand public discourse and narrative movement from structured warehouse data."

Question: What is the difference between exhibition MVP and final project?

Answer:

"The exhibition MVP is demo-ready and proves the warehouse, ETL, dashboard, Topic IQ, reports, graph, and admin flow. The final project would make the system more production-grade with scheduled ingestion, authentication, tests, richer sources, and AI enrichment."

Question: What does Topic IQ do?

Answer:

"Topic IQ lets the user search any topic and receive an intelligence-style brief. It calculates confidence, influence, strength, sentiment, evidence signals, source clusters, related narratives, and source references."

Question: What future improvements are planned?

Answer:

"Future improvements include scheduled live ingestion, larger real source datasets, DeepSeek/LLM enrichment, authentication, automated tests, upload/import audit trail, and production deployment hardening."

## Laiqa

### Role Summary

Laiqa owns the ETL, dataset, data quality, and warehouse concept explanation. Her responsibility is to explain how the data is prepared and how DW&BD concepts are used inside NarrativeIQ.

### What Laiqa Should Say

"My role was to focus on the data preparation and Data Warehousing concepts. I worked on explaining how the project data is generated, transformed, loaded, validated, and converted into dashboard-ready marts."

"The most important part of this project is the ETL and warehouse design. The dashboard becomes meaningful because it is backed by facts, dimensions, data quality metrics, materialized views, and marts."

### How Laiqa's Work Was Implemented

Laiqa's work can be explained in these steps:

1. Dataset understanding:
   - Studied the 50,000-record exhibition dataset.
   - Understood the event packs, topics, entities, sources, sentiment, and relationships.

2. ETL explanation:
   - Explained extract, transform, and load stages.
   - Connected each stage to actual project files and outputs.

3. Warehouse mapping:
   - Explained how event, source, topic, entity, sentiment, and date data become dimension tables.
   - Explained how measurable values become fact tables.

4. Data quality:
   - Explained completeness, uniqueness, consistency, timeliness, and quality score.
   - Connected these quality checks to the Data Quality dashboard.

5. Mart explanation:
   - Explained how the warehouse data is converted into dashboard-ready mart JSON.
   - Explained why mart data is useful for fast dashboard loading.

### Modules Laiqa Should Explain

#### ETL Pipeline

Say:

"ETL means Extract, Transform, Load. In NarrativeIQ, extraction creates event and narrative records, transformation calculates scores and standardizes keys, and loading writes warehouse CSV files and PostgreSQL tables."

#### Generated Dataset

Say:

"The main exhibition dashboard uses a deterministic 50,000-record dataset. It is generated to represent public discourse across events, topics, sources, sentiment, and entities."

#### Dimension Tables

Say:

"Dimension tables store context. For example, `dim_date` stores time, `dim_event` stores event information, `dim_topic` stores narrative topics, and `dim_entity` stores people, organizations, groups, and products."

#### Fact Tables

Say:

"Fact tables store measurements. For example, `fact_narrative` stores narrative strength and influence, `fact_sentiment` stores sentiment scores, and `fact_entity_mentions` stores entity mention counts."

#### Materialized Views

Say:

"Materialized views store precomputed analytical summaries. They make dashboard queries faster because the system does not need to recalculate every metric from raw facts each time."

#### Data Marts

Say:

"A data mart is a dashboard-ready analytical dataset. NarrativeIQ creates a mart JSON file that contains overview metrics, charts, graph data, replay frames, predictions, and report summaries."

#### Data Quality Dashboard

Say:

"The Data Quality dashboard shows whether the ETL outputs are complete, unique, consistent, and timely. This proves that the warehouse data is reliable for analysis."

### Laiqa Viva Questions And Answers

Question: What is ETL?

Answer:

"ETL stands for Extract, Transform, Load. Extract collects or generates data, Transform cleans and calculates useful fields, and Load stores the prepared data into warehouse outputs and PostgreSQL."

Question: What are fact tables?

Answer:

"Fact tables store measurable values. In NarrativeIQ, examples include narrative strength, sentiment score, entity mentions, trend score, engagement score, and influence score."

Question: What are dimension tables?

Answer:

"Dimension tables store descriptive context. Examples are date, source, event, topic, entity, sentiment, and live topic. Fact tables use dimension keys to avoid repeating descriptions."

Question: Why did we use a star schema?

Answer:

"We used a star schema because it is simple, fast for analytics, and easy to explain. Facts are in the center, and dimensions provide context around them."

Question: What does data quality mean in this project?

Answer:

"Data quality means checking whether warehouse outputs are complete, unique, consistent, and timely. NarrativeIQ calculates quality scores and displays them in the Data Quality module."

Question: What is the difference between warehouse data and mart data?

Answer:

"Warehouse data is the structured base layer with facts and dimensions. Mart data is a prepared analytical output made for dashboard use. The mart makes charts and modules faster and easier to load."

Question: Why use deterministic data for exhibition?

Answer:

"Deterministic data keeps the demo stable and repeatable. Live sources can fail or change during exhibition, so the generated mart proves the warehouse logic reliably. Topic IQ still adds live public-source metadata for arbitrary searched topics."

## Shared Viva Answers

Question: Is the current project complete?

Answer:

"The exhibition MVP is complete at 100%. The full final project is about 83% complete because production features like scheduled ingestion, auth, automated tests, deeper LLM enrichment, and richer source ingestion are still future work."

Question: What makes this a Data Warehousing and Big Data project?

Answer:

"It uses a high-volume dataset, ETL, fact tables, dimension tables, a star schema, PostgreSQL loading, materialized views, data marts, data quality profiling, analytics APIs, and dashboard visualization."

Question: Is Topic IQ fully live scraping?

Answer:

"Topic IQ uses lightweight public-source metadata from Wikipedia, GDELT, and Google News RSS. It is not a full scheduled scraping system yet. In the final version, scheduled ingestion would make live sources part of the main warehouse refresh."

Question: Why is the main dashboard based on generated data?

Answer:

"For exhibition reliability, the main dashboard uses deterministic generated data. This ensures stable metrics and lets us demonstrate the warehouse design clearly. The project still includes live metadata through Topic IQ and real PostgreSQL persistence for saved briefs."

Question: What should not be said?

Answer:

"Do not say the dashboard is only dummy. Say it is powered by ETL-generated mart data and FastAPI, with PostgreSQL warehouse loading and live Topic IQ persistence."

