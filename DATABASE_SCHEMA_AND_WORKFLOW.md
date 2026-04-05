# Detailed Database Architecture, Schema, and Data Workflows

This document is a comprehensive, deep-dive reference guide into the entire database architecture of the Portfolio Recommendation System. It breaks down the exact function of the SQL files used to construct the database, a meticulous dictionary of every table's attributes and relationships, and exactly how the application leverages these tables during runtime.

---

## Part 1: The SQL Files and Application Integration

Unlike traditional Django or Prisma projects that generate database tables via abstractions, this system uses a highly optimized, custom Postgres schema. Because we utilize advanced Postgres features like `TRIGGERS` and complex `VIEWS`, we rely on five explicit raw SQL files inside the `backend/sql/` folder.

Here is an exact breakdown of what each file does and how the backend utilizes them:

1.  **`schema.sql`**
    *   **What it does:** Contains the DDL (Data Definition Language) commands. It handles the `DROP TABLE IF EXISTS ... CASCADE` teardowns for clean resets, and explicitly executes 13 `CREATE TABLE` commands. It defines all strict `FOREIGN KEY` references, `UNIQUE` constraints, and Postgres `CHECK` constraints (e.g., ensuring a percentage column cannot exceed 100%). It also builds all the B-Tree `INDEXES` required for fast lookup.
2.  **`views.sql`**
    *   **What it does:** Contains `CREATE OR REPLACE VIEW` commands. Views act as virtual tables. The Streamlit app requires human-readable formatting, but the data is normalized across 13 tables. Instead of the backend executing a massive 7-table `JOIN` query repeatedly, `views.sql` pre-defines these queries directly in the database logic.
3.  **`triggers_functions.sql`**
    *   **What it does:** Pushes business logic out of Python and into the database engine for maximum speed and security. It defines custom Postgres `FUNCTION`s (like dynamically calculating a user's risk profile based on score ranges) and `TRIGGER`s (which sit and wait for `INSERT`/`UPDATE` events on specific tables to automatically populate the `audit_log` without backend Python instruction).
4.  **`seed.sql`**
    *   **What it does:** Contains thousands of rows of `INSERT INTO` statements. It acts as the "Genesis Block", pre-populating the system with Master Data: the Risk Profiles, Asset Classes, Real-world ETFs/Mutual Funds, and the mathematical % breakdown logic for the Models.
5.  **`init.sql`**
    *   **What it does:** A legacy/orchestration wrapper that can execute `\i` (include) commands to run the other 4 scripts in order if running directly via the `psql` command line tool instead of python.

### How The Application Executes These Files
When the environment is brought up, the user runs `python backend/scripts/apply_sql.py`. 
Inside `apply_sql.py`, the system establishes a synchronous connection to the NeonDB Postgres cloud server. It reads the files in explicit structural dependency order (`schema` -> `views` -> `triggers` -> `seed`), executes them as raw string blocks against the server over the internet, and securely formats the database structure.

Once formatted, the FastAPI backend uses **SQLAlchemy 2.0 ORM** to connect asynchronously and map these precise tables to Python models (`backend/app/models/`), allowing the backend application to insert user data.

---

## Part 2: Comprehensive Schema Dictionary

The system consists of 13 strongly normalized tables.

### 1. `users`
**Purpose:** Core identity and authentication.
*   `user_id` (SERIAL PRIMARY KEY): Unique identifier.
*   `name` (VARCHAR): Full name.
*   `email` (VARCHAR): **UNIQUE**. Used for login.
*   `password_hash` (TEXT): Encrypted user credentials.
*   `created_at` (TIMESTAMP): Automatically populated default.

### 2. `risk_profiles` (Seeded Master Data)
**Purpose:** Defines the rigid categories of risk tolerance.
*   `risk_profile_id` (SERIAL PRIMARY KEY): e.g., 1=Conservative, 5=Aggressive.
*   `profile_name` (VARCHAR): Human-readable name.
*   `min_score` (INT) & `max_score` (INT): Bounds for matching user scores. Has a `CHECK(min_score < max_score)`.
*   `description` (TEXT): Details on the profile.

### 3. `user_profiles`
**Purpose:** Stores a specific user's financial details and their computed risk level.
*   `profile_id` (SERIAL PRIMARY KEY)
*   `user_id` (INT): **FOREIGN KEY** -> `users(user_id)`. **UNIQUE** (1-to-1 relation). `ON DELETE CASCADE`.
*   `monthly_income`, `monthly_expenses`, `investment_amount` (NUMERIC): With `CHECK` constraints > 0.
*   `investment_horizon_years`, `investment_goal` (INT/VARCHAR)
*   `risk_score` (INT): The literal calculated math score (0-100).
*   `risk_profile_id` (INT): **FOREIGN KEY** -> `risk_profiles(risk_profile_id)`. The bucket they fell into.
*   *Interaction:* When a user's risk score changes, a DB Trigger automatically logs it.

### 4. `asset_classes` (Seeded Master Data)
**Purpose:** High-level groupings of finance (e.g., "Equity", "Debt", "Gold").
*   `asset_class_id` (SERIAL PRIMARY KEY)
*   `name` (VARCHAR) & `description` (TEXT)

### 5. `portfolio_models` (Seeded Master Data)
**Purpose:** Defines mathematical templates that can be assigned to users.
*   `model_id` (SERIAL PRIMARY KEY)
*   `model_name` (VARCHAR)
*   `risk_profile_id` (INT): **FOREIGN KEY** -> `risk_profiles`. Ties the model to the risk bucket.

### 6. `portfolio_allocations` (Seeded Master Data)
**Purpose:** Dictates exactly what percentage of a Model goes to which Asset Class (e.g., 60% Equity).
*   `allocation_id` (SERIAL PRIMARY KEY)
*   `model_id` (INT): **FOREIGN KEY** -> `portfolio_models`. `ON DELETE CASCADE`.
*   `asset_class_id` (INT): **FOREIGN KEY** -> `asset_classes`. 
*   `allocation_percentage` (NUMERIC): Has a `CHECK(<= 100 AND > 0)`.

### 7. `sub_allocation_templates` (Seeded Master Data)
**Purpose:** A junction/bridge table that creates a "bucket category" within an asset class for a specific model.
*   `template_id` (SERIAL PRIMARY KEY)
*   `model_id` (INT): **FOREIGN KEY** -> `portfolio_models`. 
*   `asset_class_id` (INT): **FOREIGN KEY** -> `asset_classes`.

### 8. `instruments` (Seeded Master Data)
**Purpose:** The actual real-world financial items (ETFs, Mutual funds) available for allocation.
*   `instrument_id` (SERIAL PRIMARY KEY)
*   `name` (VARCHAR): e.g., "Vanguard S&P 500 ETF".
*   `ticker` (VARCHAR): e.g., "VOO". 
*   `asset_class_id` (INT): **FOREIGN KEY** -> `asset_classes`.
*   `instrument_type`, `fund_house`, `is_active`

### 9. `instrument_allocations` (Seeded Master Data)
**Purpose:** Defines the granular % of an actual Instrument within a sub-allocation bucket.
*   `inst_allocation_id` (SERIAL PRIMARY KEY)
*   `template_id` (INT): **FOREIGN KEY** -> `sub_allocation_templates`.
*   `instrument_id` (INT): **FOREIGN KEY** -> `instruments`.
*   `allocation_percentage` (NUMERIC): The precise percentage share of the fund.

### 10. `user_portfolios`
**Purpose:** The generated outcome representing the entire portfolio created for the user.
*   `portfolio_id` (SERIAL PRIMARY KEY)
*   `user_id` (INT): **FOREIGN KEY** -> `users`.
*   `model_id` (INT): **FOREIGN KEY** -> `portfolio_models`. Exactly which model was applied.
*   `total_investment` (NUMERIC): Dollar amount snapshot.
*   `is_active` (BOOLEAN), `version` (INT), `generated_at` (TIMESTAMP)
*   *Interaction:* Inserting a row here fires an audit log trigger.

### 11. `user_portfolio_positions`
**Purpose:** The exact generated line-items tied to the user's specific portfolio.
*   `position_id` (SERIAL PRIMARY KEY)
*   `portfolio_id` (INT): **FOREIGN KEY** -> `user_portfolios`. `ON DELETE CASCADE`.
*   `instrument_id` (INT): **FOREIGN KEY** -> `instruments`. The exact ETF assigned.
*   `allocation_percentage` (NUMERIC): Derived percentage multiplier.
*   `allocated_amount` (NUMERIC): Literal $ amount the user should invest in this specific ticker.

### 12. `instrument_returns` (Seeded Mock Data)
**Purpose:** Tracks historical performance required for forecasting API.
*   `return_id` (SERIAL PRIMARY KEY)
*   `instrument_id` (INT): **FOREIGN KEY** -> `instruments`. 
*   `period` (VARCHAR): `CHECK(period IN ('1Y', '3Y', '5Y'))`.
*   `return_percentage` (NUMERIC): Historical performance yield.

### 13. `audit_log`
**Purpose:** Security table automatically populated by database-level triggers.
*   `log_id` (SERIAL PRIMARY KEY)
*   `user_id` (INT): **FOREIGN KEY** -> `users`.
*   `action` (VARCHAR): e.g., "PORTFOLIO_GENERATED".
*   `metadata` (JSONB): Schemaless blob storing the payload/values of the event.
*   `created_at` (TIMESTAMP).

---

## Part 3: Deep Dive into the Complete Application-to-DB Workflow

How does the Streamlit User Interface, the FastAPI Python App, and the Postgres Database engine interact to fulfill the core feature (Generating a Custom Portfolio)?

### Step 1: Data Gathering & The Profile Creation
1.  **Incoming Request:** The user fills out a React/Streamlit questionnaire and submits. The Streamlit UI sends an HTTP POST JSON payload to the FastAPI `/profiles/` endpoint.
2.  **Application Logic (Python):** `backend/app/services/profile_service.py` receives the data. It calculates a raw integer `risk_score` (0-100) based on age, income bounds, and stated goals.
3.  **Database Logic execution:** The Python application calls the Postgres function: `SELECT get_risk_profile_id(:score)`.
    *   The Postgres engine executes `triggers_functions.sql` logic, scans the `risk_profiles` table, matches the bounds, and returns a foreign key `risk_profile_id`.
4.  **Save the Results:** FastAPI invokes an SQLAlchemy `session.add()` command to `INSERT` the row into **`user_profiles`**.
    *   **The Invisible DB Trigger:** The exact millisecond the database receives the `INSERT` via the ORM, the `trg_audit_profile_update` Postgres trigger notices it, copies the newly calculated risk profile, and autonomously injects a tracking row into the **`audit_log`** table.

### Step 2: Algorithmic Routing & Generation
When the `/portfolios/generate` endpoint is called, the magic happens via traversing the 5 normalized "Model" tables (Group C):

1.  **Retrieve Strategy:** Backend looks at **`user_profiles`** to get the user's `risk_profile_id`, and then queries **`portfolio_models`** to grab the model tied to that risk bucket.
2.  **Parent Allocation Calculation:** It retrieves all rows from **`portfolio_allocations`** (`model_id` == matched). Now it knows how to split the money (e.g., 60% Equity / 40% Debt).
3.  **Child Instrument Calculation:** It traverses down to **`sub_allocation_templates`** and **`instrument_allocations`**, seeing that to fulfill the 60% Equity rule, it needs 50% "VOO" and 50% "QQQ".
4.  **Dollar Output Logic (Python):** Python mathematically resolves this: 
    *   Total Investment = $10,000. 
    *   Equity allocation = 60% ($6,000). 
    *   "VOO" instrument allocation = 50% *of the Equity bucket* ($3,000).
5.  **Final Generation Save:** The backend executes one `INSERT` into **`user_portfolios`** (Triggering another log), and multiple `INSERT` statements into **`user_portfolio_positions`** to store the precise $3000 mapping of "VOO" to the user account forever.

### Step 3: Fast Retrieval using PostgreSQL Views
When the user arrives on the Dashboard, Streamlit needs a beautifully flat, formatted table showing their names, fund houses, allocations, and prices. 

Instead of Python executing terrifying nested nested loops over 7 relations, the Database handles it natively.

1.  **API Call:** Streamlit requests `/portfolios/my-portfolio`.
2.  **View Access:** The FastAPI backend executes a devastatingly simple query against the `views.sql` created virtual table: `SELECT * FROM user_portfolio_summary WHERE user_id = {id}`
    *   Because our `schema.sql` properly indexed (`CREATE INDEX`) the tables on `user_id` and `portfolio_id`, the Postgres optimizer resolves the 7-table join instantly, passing JSON back up the pipeline array.
3.  **Forecast Charting:** Streamlit calls the forecast API. Python just runs `SELECT * FROM calculate_expected_returns(:portfolio_id)`, a complex Postgres Function that pivots and mathematically calculates projected growth against the **`instrument_returns`** table in mere milliseconds.
