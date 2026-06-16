-- Provisions one database per database-concepts module.
-- Runs automatically the first time the Postgres container is created
-- (Docker executes every file in /docker-entrypoint-initdb.d on init).
--
-- To re-run after changing this file: `docker compose down -v && docker compose up -d`.

CREATE DATABASE async_pool_demo;        -- async_sqlalchemy/
CREATE DATABASE full_text_search_demo;  -- full_text_search/
CREATE DATABASE indexes;                -- indexes/
CREATE DATABASE library;                -- db-migration-demo/ (Postgres target)
CREATE DATABASE n_plus_one_demo;        -- n_plus_one/
CREATE DATABASE normalization;          -- normalization/
CREATE DATABASE pgvector_demo;          -- pgvector-demo/
CREATE DATABASE transactions_demo;      -- transactions/
CREATE DATABASE window_functions;       -- window_functions/

-- The pgvector-demo module needs the `vector` extension enabled in its database.
\connect pgvector_demo
CREATE EXTENSION IF NOT EXISTS vector;
