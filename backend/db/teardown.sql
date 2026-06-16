-- Syntrix teardown. DEV ONLY.
-- Drops the syntrix schema (cascading every table inside it) and the two roles.
-- Run as superuser. Does not touch anything outside the syntrix schema.

\set ON_ERROR_STOP on

BEGIN;

DROP SCHEMA IF EXISTS syntrix CASCADE;

REASSIGN OWNED BY syntrix_admin TO postgres;
DROP OWNED BY syntrix_admin;
DROP ROLE IF EXISTS syntrix_admin;

REASSIGN OWNED BY syntrix_app TO postgres;
DROP OWNED BY syntrix_app;
DROP ROLE IF EXISTS syntrix_app;

COMMIT;
