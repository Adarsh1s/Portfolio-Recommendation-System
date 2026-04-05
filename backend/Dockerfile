FROM python:3.11-bullseye

WORKDIR /app

# Install system dependencies (minimal; psycopg2-binary and asyncpg use binary wheels)
RUN apt-get update && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
