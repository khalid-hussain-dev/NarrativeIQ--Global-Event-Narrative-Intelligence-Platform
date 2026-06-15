DATASET_STRATEGY.md
NarrativeIQ
Dataset & Intelligence Generation Strategy

Version: 1.0

1. Purpose

This document defines:

Data acquisition strategy
Dataset architecture
Data generation methodology
Historical simulation strategy
Narrative generation strategy
Exhibition dataset preparation

The goal is to create datasets capable of demonstrating:

Narrative evolution
Topic growth
Sentiment changes
Entity relationships
Event intelligence
Predictive analytics

without relying on unstable external APIs.

2. Core Philosophy

NarrativeIQ is NOT a social media analytics platform.

NarrativeIQ is a narrative intelligence platform.

Therefore datasets should represent:

Events
↓
Narratives
↓
Entities
↓
Evolution

not merely:

Posts
↓
Comments
↓
Charts
3. Data Source Strategy

We will use a Hybrid Data Model.

Layer A — Real Historical Data

Purpose:

Provide realism.

Sources:

Kaggle

Potential datasets:

News articles
World events
Twitter archives
Reddit discussions
Public sentiment datasets
HuggingFace Datasets

Potential datasets:

News categorization
Topic classification
Sentiment datasets
Government/Open Data

Potential datasets:

Disaster events
Economic indicators
Global events

Output:

Authentic historical records.

Layer B — Synthetic Narrative Generation

Purpose:

Create complete narrative lifecycles.

This becomes the project's secret weapon.

Example:

Event
Global AI Breakthrough

Month 1:

Low discussion volume
Positive sentiment
Few entities

Month 2:

Growing discussion
Increasing mentions
New entities appear

Month 3:

Narrative peaks
Sentiment becomes mixed
High engagement

Month 4:

Discussion declines
Narrative stabilizes

Result:

Complete lifecycle.

Perfect for demonstrations.

4. Event Categories

The system should support multiple event domains.

Technology

Examples:

AI Models
Open Source Releases
Product Launches
Sports

Examples:

World Cup
IPL
Olympics
Politics

Examples:

Elections
Policy announcements
Business

Examples:

Acquisitions
Earnings reports
Disasters

Examples:

Floods
Earthquakes
Wildfires
Entertainment

Examples:

Movies
Celebrity events
5. Narrative Lifecycle Design

Every generated narrative should follow:

Emerging
↓
Growing
↓
Peak
↓
Declining
↓
Archived
6. Narrative Generation Engine

Purpose:

Create realistic event evolution.

Generated Variables:

Discussion Volume

Represents:

Number of mentions
Sentiment

Represents:

Positive
Neutral
Negative

distribution.

Influence Score

Represents:

Narrative reach
Entity Density

Represents:

How many entities appear
7. Synthetic Dataset Architecture

Dataset:

event_master.csv

Columns:

event_id

event_name

category

region

start_date

end_date

Dataset:

narrative_history.csv

Columns:

date

event_id

topic

volume

sentiment_score

growth_rate

influence_score

Dataset:

entity_mentions.csv

Columns:

date

entity_name

entity_type

mention_count

event_id

Dataset:

sentiment_history.csv

Columns:

date

event_id

positive

neutral

negative

Dataset:

topic_trends.csv

Columns:

date

topic

trend_score

momentum
8. DeepSeek Usage Strategy

DeepSeek should NOT power the platform.

DeepSeek should enrich the platform.

Approved Uses:

Narrative Summaries

Generate:

What happened?

summaries.

Topic Classification

Assign categories.

Entity Extraction

Extract:

People
Organizations
Products
Locations
Insight Generation

Generate:

Key observations

for dashboards.

Not Approved:

Core Analytics

Never make dashboard calculations dependent on LLM responses.

9. Historical Simulation Strategy

The project should appear to contain years of intelligence.

Example:

AI Event Dataset

2023

AI Assistants

2024

Multimodal AI

2025

AI Agents

2026

Autonomous Systems

The warehouse will preserve these transitions.

This creates powerful demonstrations.

10. Entity Strategy

Entity Types:

Person

Examples:

CEOs
Politicians
Athletes

Organization

Examples:

Companies
Government agencies

Product

Examples:

AI Models
Devices
Platforms

Location

Examples:

Countries
Cities
Regions
11. Knowledge Graph Dataset

Dataset:

entity_relationships.csv

Columns:

source_entity

target_entity

relationship_type

strength_score

Examples:

OpenAI
GPT-5
CREATED
0.95
Microsoft
OpenAI
PARTNERSHIP
0.90
12. Exhibition Dataset Pack

NarrativeIQ should ship with:

Event Pack A

Artificial Intelligence

Event Pack B

Cricket World Cup

Event Pack C

Global Elections

Event Pack D

Natural Disaster Scenario

Each pack should contain:

Complete narrative lifecycle
Entity evolution
Sentiment evolution
Trend evolution
13. Dataset Scale Targets

Minimum:

50,000 records

Target:

250,000 records

Stretch Goal:

1,000,000 records
14. Data Quality Requirements

Each ETL run should calculate:

Completeness

Missing value percentage.

Consistency

Schema validation.

Uniqueness

Duplicate detection.

Accuracy

Entity validation.

Timeliness

Timestamp validation.

15. Final Dataset Principle

The dataset is not supporting the platform.

The dataset IS the platform.

All warehouse design, intelligence generation, predictions, visualizations, and demonstrations depend on the quality of the narrative history represented within the data.