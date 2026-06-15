PROJECT_CONTEXT_v2.md
NarrativeIQ
Global Event & Narrative Intelligence Platform
Codex Master Development Blueprint

Version: 2.0

Status: Architecture Frozen

1. Executive Vision

NarrativeIQ is a narrative-centric intelligence platform designed to transform fragmented digital information into historical narrative intelligence.

The platform focuses on understanding:

How events emerge
How narratives form
How public perception evolves
How entities influence discussions
How narratives rise and decline

The project is intentionally designed to demonstrate advanced Data Warehousing and Big Data concepts while providing exhibition-level visual and analytical impact.

2. Product Philosophy

Traditional systems store:

Records

NarrativeIQ stores:

Narratives

Traditional systems analyze:

Current State

NarrativeIQ analyzes:

Evolution Through Time

Every feature must support this philosophy.

3. Core Product Identity

Product Name:

NarrativeIQ

Tagline:

Transforming Digital Conversations into Narrative Intelligence

Category:

Intelligence Platform

NOT:

Dashboard
Reporting Tool
Analytics System
4. Success Criteria

A successful NarrativeIQ implementation must demonstrate:

Data Engineering
ETL pipeline
Data profiling
Data cleaning
Warehousing
Star schema
Fact tables
Dimension tables
Intelligence
Narrative detection
Entity analysis
Sentiment evolution
Visualization
Interactive dashboards
Timeline reconstruction
Relationship graphs
Prediction
Trend forecasting
Narrative growth estimation
5. Repository Structure
narrativeiq/

├── frontend/
├── backend/
├── etl/
├── warehouse/
├── analytics/
├── intelligence/
├── datasets/
├── docs/
├── scripts/
└── infrastructure/
6. Frontend Architecture

Technology:

Next.js 15
TypeScript
TailwindCSS
shadcn/ui

Visualization:

Recharts
D3.js

Structure:

frontend/src/

app/
components/
features/
hooks/
services/
types/
lib/
7. Backend Architecture

Technology:

FastAPI

Pattern:

API
↓
Service
↓
Repository
↓
Database

Structure:

backend/

api/
services/
repositories/
models/
schemas/
jobs/
middleware/
auth/
8. Database Strategy

Primary Database:

PostgreSQL

Purpose:

Warehouse
Intelligence storage
Graph storage

No MongoDB.

No Neo4j.

No unnecessary complexity.

9. Warehouse Schema
Dimension Tables
dim_date
date_key BIGINT PK

full_date DATE

day INT

month INT

quarter INT

year INT
dim_source
source_key BIGINT PK

source_name VARCHAR(255)

source_type VARCHAR(100)

platform VARCHAR(100)
dim_event
event_key BIGINT PK

event_name VARCHAR(255)

event_category VARCHAR(100)

region VARCHAR(100)

start_date TIMESTAMP

end_date TIMESTAMP
dim_entity
entity_key BIGINT PK

entity_name VARCHAR(255)

entity_type VARCHAR(100)
dim_topic
topic_key BIGINT PK

topic_name VARCHAR(255)

topic_category VARCHAR(100)
dim_sentiment
sentiment_key BIGINT PK

sentiment_label VARCHAR(50)
10. Fact Tables
fact_content
content_key BIGINT PK

date_key FK

source_key FK

event_key FK

engagement_score DECIMAL

reach_score DECIMAL

popularity_score DECIMAL
fact_sentiment
sentiment_fact_key BIGINT PK

date_key FK

event_key FK

sentiment_key FK

sentiment_score DECIMAL

polarity DECIMAL
fact_entity_mentions
mention_key BIGINT PK

entity_key FK

event_key FK

date_key FK

mention_count INT

mention_strength DECIMAL
fact_narrative
narrative_key BIGINT PK

topic_key FK

event_key FK

date_key FK

narrative_strength DECIMAL

growth_rate DECIMAL

influence_score DECIMAL
fact_trends
trend_key BIGINT PK

topic_key FK

date_key FK

trend_score DECIMAL

growth_rate DECIMAL

momentum DECIMAL
11. Knowledge Layer
entities
id BIGINT

name VARCHAR

type VARCHAR
entity_relationships
id BIGINT

source_entity_id BIGINT

target_entity_id BIGINT

relationship_strength DECIMAL
narrative_relationships
id BIGINT

source_topic_id BIGINT

target_topic_id BIGINT

similarity_score DECIMAL

Purpose:

Provide graph-based intelligence.

12. ETL Architecture

Stage 1

Data Import

Stage 2

Profiling

Metrics:

Missing values
Duplicates
Quality scores

Stage 3

Cleaning

Operations:

Deduplication
Text normalization
Date standardization

Stage 4

Enrichment

DeepSeek Tasks:

Topic assignment
Narrative summarization
Entity extraction
Sentiment analysis

Stage 5

Warehouse Loading

Stage 6

Aggregate Refresh

13. Intelligence Engine
Narrative Discovery

Detects:

Emerging narratives
Declining narratives
Narrative Clustering

Groups related discussions.

Narrative Evolution

Tracks:

Emerging
↓
Growing
↓
Peak
↓
Declining
↓
Archived
14. Entity Intelligence Engine

Capabilities:

Top entities
Fastest growing entities
Most influential entities

Outputs:

Rankings
Timelines
Graphs
15. Sentiment Intelligence Engine

Calculates:

Average sentiment
Sentiment velocity
Sentiment volatility
16. Prediction Engine

Version 1:

Moving averages
Trend forecasting

Version 2:

ML-based forecasting
17. Dashboard Inventory
Dashboard A

Executive Overview

Dashboard B

Narrative Explorer

Dashboard C

Entity Intelligence

Dashboard D

Sentiment Intelligence

Dashboard E

Prediction Center

Dashboard F

Knowledge Graph Explorer

This will likely become the exhibition centerpiece.

18. API Inventory
GET /events

GET /events/{id}

GET /narratives

GET /narratives/trending

GET /entities

GET /entities/top

GET /sentiment

GET /predictions

GET /graph
19. Codex Rules

Rule 1:

Warehouse first.

Rule 2:

No dashboard before ETL.

Rule 3:

Every chart must originate from warehouse facts.

Rule 4:

No direct dashboard access to raw datasets.

Rule 5:

All metrics must be reproducible.

Rule 6:

Backend API before frontend integration.

Rule 7:

Build intelligence engines before prediction engine.

20. Sprint Plan

Sprint 1

Foundation

Sprint 2

Warehouse

Sprint 3

ETL

Sprint 4

Intelligence Layer

Sprint 5

Knowledge Layer

Sprint 6

Dashboards

Sprint 7

Prediction

Sprint 8

Exhibition Optimization

21. Exhibition Demonstration Script

Demo Event:

Artificial Intelligence

Flow:

Show event timeline.
Show narrative evolution.
Show sentiment shifts.
Show entity graph.
Show prediction dashboard.
Show knowledge graph explorer.

Goal:

Make the judge feel they are exploring the history of an event rather than viewing a dashboard.

22. Final Architectural Principle

NarrativeIQ is not a reporting system.

NarrativeIQ is a Historical Narrative Intelligence Platform.

Every development decision must reinforce this identity.