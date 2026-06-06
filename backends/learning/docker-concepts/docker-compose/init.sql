-- Runs automatically on first PostgreSQL startup.
-- The postgres:16 image executes every *.sql file in
-- /docker-entrypoint-initdb.d/ in alphabetical order.
-- This only runs when the data directory is empty (fresh volume).

CREATE TABLE IF NOT EXISTS items (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO items (name, description) VALUES
    ('first item',  'seeded on startup'),
    ('second item', 'also seeded');
