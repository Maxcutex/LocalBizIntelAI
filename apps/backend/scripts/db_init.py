"""
Database bootstrap script.

Creates the configured Postgres database if it does not already exist.

Usage (from apps/backend):
    uv run python scripts/db_init.py

Or via Makefile:
    make db-init
"""

import sys

import psycopg

from api.config import get_settings


def ensure_database_exists() -> None:
    settings = get_settings()

    # Connect to the server-level "postgres" database to manage databases
    admin_dsn = (
        f"host={settings.pg_host} "
        f"port={settings.pg_port} "
        f"user={settings.pg_user} "
        f"password={settings.pg_password} "
        "dbname=postgres"
    )

    try:
        with psycopg.connect(admin_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (settings.pg_database,),
                )
                exists = cur.fetchone() is not None

                if exists:
                    print(f"Database '{settings.pg_database}' already exists.")
                    return

                print(f"Creating database '{settings.pg_database}'...")
                cur.execute(f'CREATE DATABASE "{settings.pg_database}"')
                print("Database created successfully.")

    except psycopg.Error as exc:
        print(f"Error while ensuring database exists: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    ensure_database_exists()


if __name__ == "__main__":
    main()


