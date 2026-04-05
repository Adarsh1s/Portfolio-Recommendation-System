# Portfolio Recommendation System - Technical & Database Architecture Guide

This document provides an in-depth, code-level explanation of the system's architecture, specifically focusing on how the backend interacts with the database. It is designed to give you a comprehensive understanding of the project's inner workings so you can easily explain it to your professor.

---

## 1. High-Level System Architecture

The application is built using a **containerized microservices architecture**. This means the frontend and backend are completely separate applications running in their own isolated Docker environments, communicating over the network.

*   **Frontend**: Built with **Streamlit** (Python). It acts as the visual client, sending REST API requests to the backend.
*   **Backend**: Built with **FastAPI** (Python). It handles business logic, security (JWT), and the core database interactions.
*   **Database**: We use a cloud-hosted Serverless Postgres solution called **NeonDB**. We do not run a Postgres database locally within Docker; instead, both the backend and our initialization commands connect directly to the cloud instance over the internet.

---

## 2. Environment Variables & The `.env` File

Instead of hardcoding sensitive database credentials directly into the Python code, the project stores them in a secure `backend/.env` file. This is a crucial security practice.

Here is what the **`.env`** file looks like:
```env
DATABASE_URL=postgresql+asyncpg://neondb_owner:YOUR_PASSWORD@ep-long-meadow-a10ypauu-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
SECRET_KEY=your-super-secret-key-change-this-in-production-minimum-32-chars
```

### How the App Reads `.env`
In `backend/app/core/config.py`, we use a library called `pydantic_settings`. This automatically grabs variables from the `.env` file and validates them when the application starts.

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    # ... other config variables

    class Config:
        env_file = ".env" # Tells Pydantic to look for our .env file

@lru_cache()
def get_settings() -> Settings:
    return Settings() # Instantiates and caches the settings in memory
```

---

## 3. Database Connection & Session Management

One of the most complex parts of a modern web application is handling database interactions efficiently. Our server uses **SQLAlchemy 2.0** with **asyncpg** to handle asynchronous (non-blocking) database calls. 

### A) The Connection Setup (`database.py`)
In `backend/app/core/database.py`, we initialize the "Engine" (which manages the connection pool to NeonDB) and the "SessionMaker" (which handles individual queries). 

Notice how the system is smart enough to parse the URL and configure SSL certificates automatically. NeonDB requires strict SSL connections, but local testing might not, so we handle it dynamically based on the URL text:

```python
# backend/app/core/database.py (snippet)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import get_settings

settings = get_settings()
db_url = settings.DATABASE_URL

# The Engine is the core connection pool connected to our cloud NeonDB
engine = create_async_engine(
    db_url,
    echo=False,           # Turn on for SQL debugging logs
    pool_pre_ping=True,   # Checks if the connection is alive before using it
    pool_size=10,         # Keeps 10 concurrent connections open
    max_overflow=20,      # Allows it to temporarily open up to 20 more connections under load
    connect_args={"ssl": True} # SSL enforced for cloud security
)

# AsyncSessionLocal is a factory that will generate new database sessions on demand
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

### B) Session Management (The Dependency Injection)
FastAPI relies heavily on "Dependency Injection". Whenever a user hits an API endpoint (e.g. asking for portfolio details), we need to give that endpoint a temporary "Session" to talk to the database, and then securely close it when done.

We use a Python `generator` function (`yield`) to do this:

```python
# backend/app/core/database.py
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session # Gives the temporary DB session to the API endpoint
        except:
            await session.rollback() # If the API endpoint crashes, discard changes!
            raise
        finally:
            await session.close() # Always safely close the connection after the API is done!
```

**How an API Router uses `get_db`:**
```python
# backend/app/routers/portfolios.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

@router.get("/my-portfolio")
async def get_portfolio(db: AsyncSession = Depends(get_db)):
    # The 'db' variable was safely provided by `get_db()`.
    # It will automatically be cleaned up when this function finishes!
    data = await db.execute(...) 
    return data
```

---

## 4. Pushing Schema & Data using Pre-made `.sql` Files

Most simple projects define their database tables in Python classes and use a tool like "Alembic" to guess how the tables should look. 

Because we needed advanced database features (like SQL `VIEWS` and `TRIGGERS`), we took a more explicitly managed approach. We rely on **raw predefined `.sql` files** to dictate exactly how the entire database should be built.

### The Structure of `backend/sql/`
*   `schema.sql`: Contains the `CREATE TABLE` setup commands (the physical structure).
*   `views.sql`: Contains `CREATE VIEW` commands (virtual tables combining data).
*   `triggers_functions.sql`: Predefined Postgres functions that execute logic when cells change.
*   `seed.sql`: Contains `INSERT INTO` commands with dummy/default data to fill the empty tables.

### Executing the Setup (`apply_sql.py`)
To build the database using these pre-made files from scratch, we run a custom Python script: `backend/scripts/apply_sql.py`.

Unlike the FastAPI web server which uses asynchronous (`asyncpg`) code, this setup script runs synchronously and sequentially using `psycopg2`, executing file after file:

```python
# backend/scripts/apply_sql.py (simplified)
import os, psycopg2

# 1. We list the pre-made files in the exact order they MUST be executed
SQL_FILES = ["schema.sql", "views.sql", "triggers_functions.sql", "seed.sql"]

def main():
    # 2. Get the DB URL and convert it to a format the simple psycopg2 driver likes
    url = os.environ.get("DATABASE_URL")
    url = url.replace("postgresql+asyncpg://", "postgresql://")

    # 3. Connect directly to NeonDB over the internet
    conn = psycopg2.connect(url)
    conn.autocommit = True # We want everything saved immediately
    cur = conn.cursor()

    base_dir = "...path_to_sql_folder..."

    # 4. Open each file, read the massive SQL strings inside, and execute them!
    for fname in SQL_FILES:
        path = os.path.join(base_dir, fname)
        with open(path, 'r', encoding='utf-8') as fh:
            sql_text = fh.read()
        cur.execute(sql_text) # Ex. Executes "CREATE TABLE USERS(...)"
    
    print("Database initialization finished.")
    conn.close()

if __name__ == '__main__':
    main()
```

---

## 5. The Exact Container Commands (Docker Execution)

When explaining this to your teacher, you can demonstrate exactly how you manage this via terminal. 

Because our Python environment is isolated inside Docker, we don't run `python apply_sql.py` on our own Windows machine. We ask the **Docker Container** to run it for us using `docker-compose exec` or `docker exec`.

### Step 1: Starting the System
First, you start up both containers (the frontend and backend):
```bash
# Run this in your root folder where docker-compose.yml lives
docker-compose up -d --build
```
*   `up`: Starts the containers.
*   `-d`: Runs them in the background (detached).
*   `--build`: Recompiles any changes made to the code.

### Step 2: Running the Database Scripts
Once the backend container is running (named `backend` inside `docker-compose.yml`), you execute the setup script **inside** that container.

Run this exact command in your terminal:
```bash
docker-compose exec backend python scripts/apply_sql.py
```
**What does this exactly do?**
1. `docker-compose exec backend`: Tells Docker to tunnel into the running "backend" container.
2. `python scripts/apply_sql.py`: Tells the Python interpreter inside the container to run our schema script.
3. The script will securely fetch the NeonDB url from `.env`, read the pre-made `.sql` files, fire them off to the cloud, and print a list of successfully generated tables in your terminal!
