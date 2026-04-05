-- ============================================================
-- Portfolio Recommendation System - Master Init Script
-- Runs automatically when PostgreSQL container starts fresh
-- ============================================================

\i /docker-entrypoint-initdb.d/schema.sql
\i /docker-entrypoint-initdb.d/views.sql
\i /docker-entrypoint-initdb.d/triggers_functions.sql
\i /docker-entrypoint-initdb.d/seed.sql
