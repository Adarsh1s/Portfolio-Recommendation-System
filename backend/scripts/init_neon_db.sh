#!/bin/sh
set -e

if [ -z "$DATABASE_URL" ]; then
  echo "DATABASE_URL is not set. Set it in backend/.env or in environment."
  exit 1
fi

# For compatibility with SQLAlchemy async URL transformer (optional)
if echo "$DATABASE_URL" | grep -q '^postgresql://'; then
  PSQURL="${DATABASE_URL/postgresql:\/\//postgresql+asyncpg://}"
else
  PSQURL="$DATABASE_URL"
fi

# In the script we need a driver-friendly URL for psql; psql accepts postgresql://
PSQL_URL="$DATABASE_URL"

echo "Waiting for database server..."
until psql "$PSQL_URL" -c '\q' 2>/dev/null; do
  echo "  - waiting for psql to connect"
  sleep 2
done

echo "Running initial schema and seed scripts on $PSQL_URL"
for f in \
  /app/sql/init.sql \
  /app/sql/schema.sql \
  /app/sql/views.sql \
  /app/sql/triggers_functions.sql \
  /app/sql/seed.sql; do
  echo "Applying $f"
  psql "$PSQL_URL" -f "$f"
done

echo "Database initialization finished."