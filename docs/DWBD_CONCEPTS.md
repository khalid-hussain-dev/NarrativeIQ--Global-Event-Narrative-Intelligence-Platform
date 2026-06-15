# NarrativeIQ DW&BD Working Notes

This document explains how NarrativeIQ uses Data Warehousing and Big Data concepts in the current project build.

## 1. System Working

NarrativeIQ is organized as a warehouse-first intelligence system:

1. `etl/pipeline.py` generates raw narrative/event/content records.
2. The ETL pipeline cleans, profiles, transforms, and writes warehouse CSV outputs.
3. `warehouse/001_schema.sql` defines the PostgreSQL star-schema warehouse.
4. `etl/load_postgres.py` loads CSV warehouse outputs into PostgreSQL.
5. `warehouse/002_materialized_views.sql` creates aggregated analytical views.
6. FastAPI reads the generated mart JSON and exposes dashboard/admin/topic intelligence APIs.
7. Topic IQ can also call lightweight public-source metadata providers and save live snapshots into PostgreSQL.
8. The Next.js frontend visualizes metrics, replay, graph, predictions, reports, admin controls, Topic IQ, and saved live-topic history.

The main dashboard mart is synthetic and deterministic. It simulates public discourse from source categories such as news, social, forums, and sports wires. Topic IQ adds live public-source metadata from Wikipedia, GDELT, and Google News RSS, then can persist those topic snapshots into PostgreSQL.

## 2. ETL Concepts

ETL means Extract, Transform, Load.

### Extract

Current extract stage:

- Reads deterministic event/topic/entity definitions from `etl/pipeline.py`.
- Generates simulated raw content records.
- Creates event, narrative, sentiment, trend, entity, and relationship datasets.

In the current exhibition version, Topic IQ already extends this layer with lightweight public-source metadata. In a future production version, the full mart refresh can be driven by scheduled real APIs, CSV files, web data, Reddit/X/news feeds, or uploaded datasets.

### Transform

Transformation is where raw/generated data becomes warehouse-ready:

- Dates are converted into integer `date_key` values.
- Source names become `source_key`.
- Events become `event_key`.
- Topics become `topic_key`.
- Entities become `entity_key`.
- Sentiment labels become `sentiment_key`.
- Narrative strength, growth rate, influence score, lifecycle stage, sentiment score, trend score, and momentum are calculated.
- Data quality metrics are generated for every output dataset.

This is the most important DW&BD part because raw content is not directly suitable for analytics. It must be structured into dimensions and facts.

### Load

Load happens in two layers:

- CSV load: ETL writes warehouse CSV files to `datasets/warehouse/`.
- PostgreSQL load: `etl/load_postgres.py` loads those CSV files into the PostgreSQL schema.

The real PostgreSQL load has been verified for the local database `narrativeiq`.

## 3. Star Schema

NarrativeIQ uses a star schema. A star schema has:

- Dimension tables: descriptive context.
- Fact tables: measurable events or transactions.

Dimensions sit around facts like points around a star.

## 4. Dimension Tables

Dimension tables answer: who, what, where, when, and what category?

### `dim_date`

Stores date context:

- `date_key`
- full date
- day
- week
- month
- quarter
- year

Fact tables use `date_key` instead of repeating full date details.

### `dim_source`

Stores simulated source metadata:

- source id
- source name
- source type
- platform

Example source types include news, social, discussion forum, and sports wire.

### `dim_event`

Stores major event clusters:

- Artificial Intelligence Revolution
- Cricket World Cup
- Global Elections
- Natural Disaster Response

Each event has category, region, start date, and end date.

### `dim_topic`

Stores narrative topics such as:

- AI Agents
- AI Governance
- Election Security
- Climate Risk

Topics are linked to facts through `topic_key`.

### `dim_entity`

Stores entities found in narratives:

- organizations
- people
- products
- groups
- locations
- topics

Examples: OpenAI, Microsoft, ICC, Babar Azam, Election Commission.

### `dim_sentiment`

Stores sentiment categories:

- Positive
- Neutral
- Negative

## 5. Fact Tables

Fact tables answer: how much, how often, how strong, and how fast?

### `fact_content`

Main content fact table.

Measures:

- engagement score
- reach score
- popularity score

Connected dimensions:

- date
- source
- event
- topic
- sentiment

This table represents the raw content activity layer.

### `fact_narrative`

Tracks narrative lifecycle and strength.

Measures:

- narrative strength
- growth rate
- influence score
- lifecycle stage

This drives the dashboard narrative charts and replay mode.

### `fact_sentiment`

Tracks sentiment over time.

Measures:

- sentiment score
- polarity
- content count

This powers sentiment distribution and timeline analytics.

### `fact_trends`

Tracks topic trend velocity.

Measures:

- trend score
- growth rate
- momentum

This powers top growing topics and trend charts.

### `fact_entity_mentions`

Tracks entity influence.

Measures:

- mention count
- mention strength

This powers entity ranking and influence analysis.

### `entity_relationships`

Stores graph relationships between entities/topics.

Measures:

- relationship type
- strength score

This powers the knowledge graph.

### `dim_live_topic`

Stores searched live topics from Topic IQ:

- topic key
- topic name
- canonical title
- first seen time
- last seen time

This proves arbitrary searched topics can be persisted beyond the UI.

### `fact_live_topic_snapshot`

Stores each saved live-topic measurement.

Measures:

- confidence
- narrative strength
- influence score
- sentiment score
- lifecycle stage
- total signals
- news signals
- reference signals
- source clusters

This is the bridge between on-demand live ingestion and warehouse-style historical analysis.

### `live_topic_sources`

Stores the reference/news source rows behind a saved live topic snapshot.

Fields:

- source type
- source title
- source URL
- source domain
- published timestamp

## 6. Data Quality Profiling

The ETL creates `data_quality_report.csv` and loads it into `etl_quality_report`.

Quality dimensions:

- completeness
- uniqueness
- consistency
- timeliness
- overall quality score

The dashboard uses this to prove that ETL profiling exists.

## 7. Materialized Views

Materialized views are precomputed analytical tables. They make dashboards faster because aggregations are already calculated.

NarrativeIQ defines views such as:

- narrative overview
- sentiment evolution
- entity influence
- trend velocity

They are refreshed after PostgreSQL load.

## 8. Data Marts

A data mart is a smaller analytics-ready dataset created from the warehouse for a specific use case.

NarrativeIQ writes:

```text
datasets/marts/narrativeiq_mart.json
```

This mart powers:

- dashboard overview
- replay frames
- graph nodes and links
- predictions
- reports
- Topic IQ briefs

## 9. Topic IQ Working

Topic IQ is the first step toward the original "search any topic" vision.

When the user enters a topic:

1. FastAPI receives the query at `/topic-intelligence?q=...`.
2. The API first attempts live public-source context using Wikipedia topic context and public news metadata.
3. If live context is available, it returns `mode: live_ingestion`.
4. If live context fails, it tokenizes the query and compares it against warehouse mart events, narratives, entities, and categories.
5. It returns `mode: warehouse_match` for a direct mart match or `mode: prospective_brief` for a best-effort warehouse fallback.
6. It returns a topic brief with:
   - summary
   - confidence
   - event cluster
   - influence score
   - narrative strength
   - sentiment
   - lifecycle stage
   - related narratives
   - influence entities
   - timeline

The user can click Save Brief after generation. Saved live topics are stored in PostgreSQL using:

- `dim_live_topic`
- `fact_live_topic_snapshot`
- `live_topic_sources`

This makes live topic search part of the warehouse story instead of only an API response.

## 10. Dashboard Working

The frontend calls FastAPI first. If FastAPI is unavailable, it falls back to bundled mart JSON.

Main modules:

- Overview: executive metrics.
- Topic IQ: search any topic, generate a live-source brief, save it, and reload saved warehouse snapshots.
- Events: event-level intelligence.
- Sentiment: sentiment distribution.
- Replay: month-by-month narrative lifecycle playback.
- Graph: entity and narrative relationship graph.
- Predictions: forecast-like narrative movement.
- Data Quality: ETL quality profile.
- Reports: branded report preview/export.
- Administration: ETL and PostgreSQL loader controls.

## 11. What Is Real vs Simulated

Real:

- ETL pipeline
- CSV warehouse outputs
- PostgreSQL schema
- PostgreSQL load
- dimension/fact modeling
- quality profiling
- materialized views
- FastAPI endpoints
- dashboard interactions
- report generation
- Topic IQ live public-source context and warehouse fallback logic
- saved live-topic dimension/fact/source tables

Simulated:

- warehouse source content records
- warehouse source platforms
- warehouse narrative event data
- generated sentiment values
- generated entity mention counts
- generated trend/influence scores

Future extension:

- richer external source coverage
- DeepSeek/OpenAI summaries
- live refresh jobs
- automated production deployment
