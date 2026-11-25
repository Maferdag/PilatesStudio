CREATE ROLE pilates_app
    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
    NOREPLICATION NOBYPASSRLS;

ALTER ROLE pilates_app WITH PASSWORD 'PilatesStudio123';


SELECT rolname, rolsuper, rolbypassrls, rolcanlogin
FROM pg_roles
WHERE rolname = 'pilates_app';
