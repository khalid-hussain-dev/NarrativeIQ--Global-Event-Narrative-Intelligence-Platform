CREATE SCHEMA IF NOT EXISTS narrativeiq;

SET search_path TO narrativeiq;

CREATE TABLE IF NOT EXISTS dim_live_topic (
    topic_key BIGSERIAL PRIMARY KEY,
    topic_name VARCHAR(255) NOT NULL UNIQUE,
    canonical_title VARCHAR(255) NOT NULL,
    first_seen_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fact_live_topic_snapshot (
    snapshot_key BIGSERIAL PRIMARY KEY,
    topic_key BIGINT NOT NULL REFERENCES dim_live_topic(topic_key),
    measured_at TIMESTAMP NOT NULL DEFAULT NOW(),
    mode VARCHAR(60) NOT NULL,
    confidence NUMERIC(8, 2) NOT NULL,
    narrative_strength NUMERIC(8, 2) NOT NULL,
    influence_score NUMERIC(8, 2) NOT NULL,
    sentiment_score NUMERIC(8, 4) NOT NULL,
    sentiment_label VARCHAR(50) NOT NULL,
    lifecycle_stage VARCHAR(50) NOT NULL,
    total_signals INT NOT NULL,
    news_signals INT NOT NULL,
    reference_signals INT NOT NULL,
    source_clusters INT NOT NULL,
    summary TEXT NOT NULL,
    source_note TEXT NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS live_topic_sources (
    source_key BIGSERIAL PRIMARY KEY,
    snapshot_key BIGINT NOT NULL REFERENCES fact_live_topic_snapshot(snapshot_key) ON DELETE CASCADE,
    source_type VARCHAR(80) NOT NULL,
    source_title TEXT NOT NULL,
    source_url TEXT,
    source_domain VARCHAR(255),
    published_at VARCHAR(80)
);

CREATE INDEX IF NOT EXISTS idx_dim_live_topic_name
ON dim_live_topic(topic_name);

CREATE INDEX IF NOT EXISTS idx_fact_live_topic_snapshot_topic_time
ON fact_live_topic_snapshot(topic_key, measured_at DESC);
