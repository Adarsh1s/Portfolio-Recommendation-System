# Portfolio Recommendation System
### DBMS Project — FastAPI · PostgreSQL · Streamlit · Docker

A full-stack financial application that recommends investment portfolios based on a user's risk profile. Built as a DBMS case study demonstrating normalization, stored procedures, triggers, views, and transaction management.

---

## Tech Stack

| Layer    | Technology                            |
|----------|---------------------------------------|
| Frontend | Streamlit 1.33 · Plotly               |
| Backend  | FastAPI · Python 3.11 · SQLAlchemy    |
| Database | PostgreSQL 16                         |
| Auth     | JWT (access token) + HttpOnly cookies |
| Deploy   | Docker Compose (2 services)           |

> Redis has been intentionally excluded. Rate limiting uses `slowapi` with an in-process memory backend.

---

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- For **Neon DB:** outbound TCP 5432 access (no VPN blocking)
- Free ports: `8001` (backend), `8502` (frontend) — or override via env vars

### 1. Clone and configure

```bash
git clone <repo-url>
cd portfolio-recommendation-system
```

Create `backend/.env`:
```bash
# Neon database URL (copy from your Neon project settings)
DATABASE_URL=postgresql+asyncpg://<username>:<password>@<host>/<db>?sslmode=require&channel_binding=require

# Auth secret (minimum 32 characters)
SECRET_KEY=your-super-secret-key-change-this-in-production-minimum-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256
CORS_ORIGINS=http://localhost:8501,http://frontend:8501
```

### 2. Initialize Neon database (schema + seed)

**Option A: Using Python script inside Docker (Recommended)**
```bash
docker-compose build backend
docker-compose run --rm backend python scripts/apply_sql.py
```

Expected output:
```
Using DB URL: postgresql://...
Applying: /app/sql/schema.sql
Applying: /app/sql/views.sql
Applying: /app/sql/triggers_functions.sql
Applying: /app/sql/seed.sql

Listing user tables:
- public.users
- public.risk_profiles
- public.user_profiles
- ... (13 tables total)

Database initialization finished.
```

**Option B: Manual paste into Neon Dashboard (if network blocks port 5432)**
1. Open your Neon project → SQL Editor
2. Open `backend/sql/all_for_neon.sql` from this repo
3. Copy all SQL → paste into Neon console → Run
4. Verify: your DB now has 13 tables and seed data

### 3. Build and start services

```bash
# Default ports: backend 8001, frontend 8502
docker-compose up --build backend frontend
```

Or use custom ports:
```bash
BACKEND_HOST_PORT=9000 FRONTEND_HOST_PORT=9501 docker-compose up --build backend frontend
```

### 4. Access the application

| Service   | Default URL              | Notes                    |
|-----------|--------------------------|--------------------------|
| Frontend  | http://localhost:8502    | Streamlit dashboard      |
| API Docs  | http://localhost:9000/docs | FastAPI Swagger UI      |
| Database  | Neon cloud               | No local database        |

### 5. Stop services

```bash
docker-compose down          # stop containers, keep data
docker-compose down -v       # remove all (fresh next run)
```

---

## For Other Machines

### Clone and Setup (Linux / macOS / Windows WSL2)

```bash
# 1. Clone repo
git clone <repo-url>
cd portfolio-recommendation-system

# 2. Set environment (Neon URL from your dashboard)
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql+asyncpg://<username>:<password>@<host>/<db>?sslmode=require&channel_binding=require
SECRET_KEY=your-secret-key-32-chars-minimum
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256
CORS_ORIGINS=http://localhost:8501,http://frontend:8501
EOF

# 3. Build images
docker-compose build

# 4. Initialize schema + seed in Neon
docker-compose run --rm backend python scripts/apply_sql.py

# 5. Start all services
docker-compose up backend frontend
```

**All-in-one command:**
```bash
git clone <repo-url> && cd portfolio-recommendation-system && \
cp backend/.env.example backend/.env && \
# Edit backend/.env manually with your Neon credentials, then:
docker-compose build && \
docker-compose run --rm backend python scripts/apply_sql.py && \
docker-compose up backend frontend
```

### Troubleshooting on Other Machines

**Port already in use:**
```bash
# Override default ports
BACKEND_HOST_PORT=8002 FRONTEND_HOST_PORT=8503 docker-compose up
```

**Can't connect to Neon (connection refused):**
- Check firewall allows outbound TCP 5432
- Verify your Neon URL is correct (check dashboard)
- Try manual paste method using `backend/sql/all_for_neon.sql`

**Database already initialized?**
```bash
# Re-apply schema (drops and recreates all tables)
docker-compose run --rm backend python scripts/apply_sql.py
```

**Container won't start (health check fails):**
```bash
# Check backend logs
docker-compose logs backend

# Ensure DATABASE_URL in backend/.env is valid:
cat backend/.env | grep DATABASE_URL
```

---

## User Journey

1. **Register / Login** → `app.py`
2. **Complete Financial Profile** → income, expenses, investment amount, horizon, goal
3. **Take Risk Questionnaire** → 7 MCQ questions → risk score (0–100)
4. **Generate Portfolio** → transaction creates versioned portfolio with all positions
5. **View Dashboard** → pie chart, instrument table, expected returns
6. **Compare** → side-by-side comparison with any risk profile model
7. **History** → all previous portfolio versions

---

## Database Schema (13 Tables)

```
users                    → Core authentication
risk_profiles            → Conservative / Mod Conservative / Moderate / Aggressive
user_profiles            → Financial data + computed risk score
asset_classes            → Equity / Debt / Gold / Cash / International / Real Estate
portfolio_models         → 4 model templates, one per risk profile
portfolio_allocations    → % split by asset class per model
sub_allocation_templates → Bridge between model and instrument groups
instruments              → 30 Indian market instruments (ETFs, MFs, bonds, REITs)
instrument_allocations   → % per instrument within each template
user_portfolios          → Generated portfolio instances (versioned)
user_portfolio_positions → Individual instrument positions
instrument_returns       → 1Y / 3Y / 5Y mock return data
audit_log                → Auto-populated by trigger on portfolio generation
```

---

## Advanced DBMS Features

### Views (4)
- `user_portfolio_summary` — 7-table join for dashboard
- `asset_class_summary` — aggregated pie chart data
- `portfolio_model_overview` — for Compare page
- `instrument_with_returns` — pivoted 1Y/3Y/5Y returns

### Triggers (3)
- `trg_audit_portfolio` — auto-logs every portfolio generation
- `trg_audit_profile_update` — logs risk score changes
- `trg_user_profiles_updated_at` — keeps `updated_at` fresh

### PL/pgSQL Functions (4)
- `get_risk_profile_id(score)` — maps score to risk profile
- `get_portfolio_model_for_user(user_id)` — returns model for user
- `calculate_expected_returns(portfolio_id)` — blended weighted returns
- `validate_allocation_sums()` — post-seed integrity check

### Transactions
Portfolio generation runs in a single atomic transaction:
1. Deactivate old portfolio (`UPDATE`)
2. Insert new portfolio row — trigger fires automatically
3. Bulk-insert all positions via multi-table `INSERT ... SELECT`

---

## API Endpoints

### Auth
| Method | Endpoint          |
|--------|-------------------|
| POST   | /auth/register    |
| POST   | /auth/login       |
| POST   | /auth/refresh     |
| POST   | /auth/logout      |

### Profile & Questionnaire
| Method | Endpoint                   |
|--------|----------------------------|
| POST   | /profile/create            |
| PUT    | /profile/update            |
| GET    | /profile/me                |
| GET    | /questionnaire/questions   |
| POST   | /questionnaire/submit      |

### Portfolio
| Method | Endpoint                          |
|--------|-----------------------------------|
| POST   | /portfolio/generate               |
| GET    | /portfolio/current                |
| GET    | /portfolio/history                |
| GET    | /portfolio/summary                |
| GET    | /portfolio/expected-returns       |
| GET    | /portfolio/compare/{risk_level}   |

### Reference
| Method | Endpoint              |
|--------|-----------------------|
| GET    | /instruments          |
| GET    | /risk-profiles        |
| GET    | /portfolio-models     |

---

## Project Structure

```
portfolio-recommendation-system/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/          (config, database, security)
│   │   ├── models/        (SQLAlchemy ORM)
│   │   ├── schemas/       (Pydantic v2)
│   │   ├── routers/       (auth, profile, questionnaire, portfolio, reference)
│   │   └── services/      (risk_engine, portfolio_engine)
│   ├── sql/               (schema, seed, views, triggers, init)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── app.py             (Login / Register)
│   ├── pages/
│   │   ├── 1_Onboarding.py
│   │   ├── 2_Questionnaire.py
│   │   ├── 3_Dashboard.py
│   │   ├── 4_History.py
│   │   ├── 5_Compare.py
│   │   └── 6_Profile.py
│   ├── utils/             (api.py, charts.py)
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## Validation Queries

Run these after startup to verify data integrity:

```sql
-- Verify allocation sums = 100% per model
SELECT * FROM validate_allocation_sums();

-- Check all views work
SELECT COUNT(*) FROM user_portfolio_summary;
SELECT COUNT(*) FROM instrument_with_returns;

-- Verify seed counts
SELECT COUNT(*) FROM instruments;          -- 30
SELECT COUNT(*) FROM instrument_returns;   -- 90
SELECT COUNT(*) FROM instrument_allocations; -- ~60
```

---

*All instrument data is illustrative. Not financial advice.*
