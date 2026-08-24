-- The "application" database the platform keeps reliable. pg_stat_statements
-- lets the sentinel see slow queries; pg_stat_activity lets it see and kill
-- runaway sessions.

CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- A tiny bit of app data so there's something to query.
CREATE TABLE IF NOT EXISTS orders (
    id          BIGSERIAL PRIMARY KEY,
    customer    TEXT NOT NULL,
    total_cents BIGINT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO orders (customer, total_cents)
SELECT 'customer-' || g, (random() * 100000)::bigint
FROM generate_series(1, 1000) g;
