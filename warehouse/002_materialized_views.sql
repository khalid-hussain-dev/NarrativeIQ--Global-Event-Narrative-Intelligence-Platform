SET search_path TO narrativeiq;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_narrative_overview AS
SELECT
    e.event_id,
    e.event_name,
    t.topic_name,
    d.full_date,
    fn.narrative_strength,
    fn.growth_rate,
    fn.influence_score,
    fn.lifecycle_stage
FROM fact_narrative fn
JOIN dim_event e ON e.event_key = fn.event_key
JOIN dim_topic t ON t.topic_key = fn.topic_key
JOIN dim_date d ON d.date_key = fn.date_key;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_sentiment_evolution AS
SELECT
    e.event_id,
    e.event_name,
    d.full_date,
    s.sentiment_label,
    SUM(fs.content_count) AS content_count,
    AVG(fs.sentiment_score) AS sentiment_score
FROM fact_sentiment fs
JOIN dim_event e ON e.event_key = fs.event_key
JOIN dim_sentiment s ON s.sentiment_key = fs.sentiment_key
JOIN dim_date d ON d.date_key = fs.date_key
GROUP BY e.event_id, e.event_name, d.full_date, s.sentiment_label;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_entity_influence AS
SELECT
    ent.entity_name,
    ent.entity_type,
    e.event_name,
    SUM(fem.mention_count) AS total_mentions,
    AVG(fem.mention_strength) AS avg_mention_strength
FROM fact_entity_mentions fem
JOIN dim_entity ent ON ent.entity_key = fem.entity_key
JOIN dim_event e ON e.event_key = fem.event_key
GROUP BY ent.entity_name, ent.entity_type, e.event_name;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_trend_velocity AS
SELECT
    t.topic_name,
    e.event_name,
    d.full_date,
    ft.trend_score,
    ft.growth_rate,
    ft.momentum
FROM fact_trends ft
JOIN dim_topic t ON t.topic_key = ft.topic_key
JOIN dim_event e ON e.event_key = ft.event_key
JOIN dim_date d ON d.date_key = ft.date_key;

CREATE INDEX IF NOT EXISTS idx_mv_narrative_overview_event_date
ON mv_narrative_overview(event_id, full_date);

CREATE INDEX IF NOT EXISTS idx_mv_entity_influence_mentions
ON mv_entity_influence(total_mentions);
