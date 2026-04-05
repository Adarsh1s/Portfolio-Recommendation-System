#!/usr/bin/env python3
import os
import sys
import psycopg2

SQL_FILES = [
    # Skip init.sql — it only contains `\i` directives (psycopg2 doesn't support \i)
    # "init.sql",
    "schema.sql",
    "views.sql",
    "triggers_functions.sql",
    "seed.sql",
]


def main():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set. Set it in backend/.env or environment.")
        sys.exit(1)

    # Convert asyncuri to a psycopg2-friendly URI
    if url.startswith("postgresql+asyncpg://"):
        psql_url = "postgresql://" + url[len("postgresql+asyncpg://"):]
    else:
        psql_url = url

    print("Using DB URL:", psql_url)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sql'))

    try:
        conn = psycopg2.connect(psql_url)
        conn.autocommit = True
    except Exception as e:
        print("Failed to connect to database:", e)
        sys.exit(2)

    try:
        with conn.cursor() as cur:
            for fname in SQL_FILES:
                path = os.path.join(base_dir, fname)
                if not os.path.exists(path):
                    print("Skipping missing:", path)
                    continue
                print("Applying:", path)
                with open(path, 'r', encoding='utf-8') as fh:
                    sql_text = fh.read()
                cur.execute(sql_text)

            # List created tables for verification
            print("\nListing user tables:")
            cur.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog','information_schema')
                ORDER BY table_schema, table_name
            """)
            rows = cur.fetchall()
            if not rows:
                print("(no user tables found)")
            else:
                for schema, table in rows:
                    print(f"- {schema}.{table}")

        print("\nDatabase initialization finished.")
    except Exception as e:
        print("Error while applying SQL:", e)
        sys.exit(3)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
