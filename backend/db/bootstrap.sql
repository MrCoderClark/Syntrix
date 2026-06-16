-- Syntrix database bootstrap.
-- Run ONCE as a Postgres superuser against the Supabase Postgres.
-- Idempotent: re-running is safe.
--
-- Usage (via docker exec into the Supabase db container):
--   docker exec -i supabase-db psql -U postgres -d postgres \
--        -v syntrix_admin_password="'<SET_ME>'" \
--        -v syntrix_app_password="'<SET_ME>'" \
--        < backend/db/bootstrap.sql
--
-- The passwords are passed as psql variables and substituted below.
-- Inside DO blocks, use EXECUTE with format() since psql variables
-- don't expand inside $$ strings.

\set ON_ERROR_STOP on

BEGIN;

-- ---- Extensions (IF NOT EXISTS — safe alongside existing data) ----
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS ltree;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---- Roles ----
-- Role creation is non-transactional in Postgres, so we use DO blocks
-- with dynamic SQL to handle idempotency.
DO $body$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'syntrix_admin') THEN
    EXECUTE format('CREATE ROLE syntrix_admin LOGIN PASSWORD %L', :syntrix_admin_password);
  ELSE
    EXECUTE format('ALTER ROLE syntrix_admin WITH LOGIN PASSWORD %L', :syntrix_admin_password);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'syntrix_app') THEN
    EXECUTE format('CREATE ROLE syntrix_app LOGIN PASSWORD %L', :syntrix_app_password);
  ELSE
    EXECUTE format('ALTER ROLE syntrix_app WITH LOGIN PASSWORD %L', :syntrix_app_password);
  END IF;
END
$body$;

-- Grant syntrix_admin to the superuser so it can CREATE SCHEMA with
-- AUTHORIZATION (requires membership in the target role).
GRANT syntrix_admin TO postgres;

-- ---- Schema (all Syntrix tables live here — never in public) ----
CREATE SCHEMA IF NOT EXISTS syntrix AUTHORIZATION syntrix_admin;

-- ---- Schema-level grants ----
-- syntrix_app gets USAGE only (no CREATE — forces all DDL through Alembic).
GRANT USAGE ON SCHEMA syntrix TO syntrix_app;

-- ---- Default privileges ----
-- When syntrix_admin creates tables/sequences/functions in syntrix,
-- syntrix_app automatically gets CRUD. No manual re-grant after migrations.
ALTER DEFAULT PRIVILEGES FOR ROLE syntrix_admin IN SCHEMA syntrix
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO syntrix_app;
ALTER DEFAULT PRIVILEGES FOR ROLE syntrix_admin IN SCHEMA syntrix
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO syntrix_app;
ALTER DEFAULT PRIVILEGES FOR ROLE syntrix_admin IN SCHEMA syntrix
  GRANT EXECUTE ON FUNCTIONS TO syntrix_app;

-- ---- Per-role search_path ----
ALTER ROLE syntrix_admin IN DATABASE postgres SET search_path = syntrix, public;
ALTER ROLE syntrix_app   IN DATABASE postgres SET search_path = syntrix, public;

COMMIT;
