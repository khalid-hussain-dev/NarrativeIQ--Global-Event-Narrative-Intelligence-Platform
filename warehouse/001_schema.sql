CREATE SCHEMA IF NOT EXISTS narrativeiq;

SET search_path TO narrativeiq;

CREATE TABLE IF NOT EXISTS dim_date (
    date_key BIGINT PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day INT NOT NULL,
    week INT NOT NULL,
    month INT NOT NULL,
    quarter INT NOT NULL,
    year INT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_source (
    source_key BIGSERIAL PRIMARY KEY,
    source_id VARCHAR(100) NOT NULL UNIQUE,
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    platform VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_event (
    event_key BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(100) NOT NULL UNIQUE,
    event_name VARCHAR(255) NOT NULL,
    event_category VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE
);

CREATE TABLE IF NOT EXISTS dim_entity (
    entity_key BIGSERIAL PRIMARY KEY,
    entity_name VARCHAR(255) NOT NULL UNIQUE,
    entity_type VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_topic (
    topic_key BIGSERIAL PRIMARY KEY,
    topic_name VARCHAR(255) NOT NULL UNIQUE,
    topic_category VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_sentiment (
    sentiment_key BIGSERIAL PRIMARY KEY,
    sentiment_label VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS fact_content (
    content_key BIGSERIAL PRIMARY KEY,
    date_key BIGINT NOT NULL REFERENCES dim_date(date_key),
    source_key BIGINT NOT NULL REFERENCES dim_source(source_key),
    event_key BIGINT NOT NULL REFERENCES dim_event(event_key),
    topic_key BIGINT NOT NULL REFERENCES dim_topic(topic_key),
    sentiment_key BIGINT NOT NULL REFERENCES dim_sentiment(sentiment_key),
    engagement_score NUMERIC(12, 2) NOT NULL,
    reach_score NUMERIC(12, 2) NOT NULL,
    popularity_score NUMERIC(12, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_sentiment (
    sentiment_fact_key BIGSERIAL PRIMARY KEY,
    date_key BIGINT NOT NULL REFERENCES dim_date(date_key),
    event_key BIGINT NOT NULL REFERENCES dim_event(event_key),
    sentiment_key BIGINT NOT NULL REFERENCES dim_sentiment(sentiment_key),
    sentiment_score NUMERIC(8, 4) NOT NULL,
    polarity NUMERIC(8, 4) NOT NULL,
    content_count INT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_entity_mentions (
    mention_key BIGSERIAL PRIMARY KEY,
    entity_key BIGINT NOT NULL REFERENCES dim_entity(entity_key),
    event_key BIGINT NOT NULL REFERENCES dim_event(event_key),
    date_key BIGINT NOT NULL REFERENCES dim_date(date_key),
    mention_count INT NOT NULL,
    mention_strength NUMERIC(8, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_narrative (
    narrative_fact_key BIGSERIAL PRIMARY KEY,
    topic_key BIGINT NOT NULL REFERENCES dim_topic(topic_key),
    event_key BIGINT NOT NULL REFERENCES dim_event(event_key),
    date_key BIGINT NOT NULL REFERENCES dim_date(date_key),
    narrative_strength NUMERIC(8, 2) NOT NULL,
    growth_rate NUMERIC(8, 2) NOT NULL,
    influence_score NUMERIC(8, 2) NOT NULL,
    lifecycle_stage VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_trends (
    trend_key BIGSERIAL PRIMARY KEY,
    topic_key BIGINT NOT NULL REFERENCES dim_topic(topic_key),
    event_key BIGINT NOT NULL REFERENCES dim_event(event_key),
    date_key BIGINT NOT NULL REFERENCES dim_date(date_key),
    trend_score NUMERIC(8, 2) NOT NULL,
    growth_rate NUMERIC(8, 2) NOT NULL,
    momentum NUMERIC(8, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS entity_relationships (
    relationship_key BIGSERIAL PRIMARY KEY,
    source_entity_key BIGINT NOT NULL REFERENCES dim_entity(entity_key),
    target_entity_key BIGINT NOT NULL REFERENCES dim_entity(entity_key),
    relationship_type VARCHAR(100) NOT NULL,
    strength_score NUMERIC(8, 4) NOT NULL
);

CREATE TABLE IF NOT EXISTS etl_quality_report (
    quality_key BIGSERIAL PRIMARY KEY,
    dataset VARCHAR(255) NOT NULL,
    record_count BIGINT NOT NULL,
    completeness NUMERIC(8, 2) NOT NULL,
    uniqueness NUMERIC(8, 2) NOT NULL,
    consistency NUMERIC(8, 2) NOT NULL,
    timeliness NUMERIC(8, 2) NOT NULL,
    quality_score NUMERIC(8, 2) NOT NULL,
    measured_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fact_content_date ON fact_content(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_content_event ON fact_content(event_key);
CREATE INDEX IF NOT EXISTS idx_fact_narrative_event_date ON fact_narrative(event_key, date_key);
CREATE INDEX IF NOT EXISTS idx_fact_narrative_topic_date ON fact_narrative(topic_key, date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sentiment_event_date ON fact_sentiment(event_key, date_key);
CREATE INDEX IF NOT EXISTS idx_fact_entity_mentions_entity_date ON fact_entity_mentions(entity_key, date_key);
CREATE INDEX IF NOT EXISTS idx_fact_trends_topic_date ON fact_trends(topic_key, date_key);
