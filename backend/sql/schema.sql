-- ============================================================
-- Portfolio Recommendation System - Full Schema DDL
-- 13 tables: users, risk_profiles, user_profiles, asset_classes,
-- portfolio_models, portfolio_allocations, sub_allocation_templates,
-- instruments, instrument_allocations, user_portfolios,
-- user_portfolio_positions, instrument_returns, audit_log
-- ============================================================

-- Drop in reverse dependency order (for clean reruns)
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS instrument_returns CASCADE;
DROP TABLE IF EXISTS user_portfolio_positions CASCADE;
DROP TABLE IF EXISTS user_portfolios CASCADE;
DROP TABLE IF EXISTS instrument_allocations CASCADE;
DROP TABLE IF EXISTS instruments CASCADE;
DROP TABLE IF EXISTS sub_allocation_templates CASCADE;
DROP TABLE IF EXISTS portfolio_allocations CASCADE;
DROP TABLE IF EXISTS portfolio_models CASCADE;
DROP TABLE IF EXISTS asset_classes CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS risk_profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop functions and triggers if they exist
DROP FUNCTION IF EXISTS fn_audit_portfolio_generation() CASCADE;
DROP FUNCTION IF EXISTS get_risk_profile_id(INT) CASCADE;
DROP VIEW IF EXISTS user_portfolio_summary CASCADE;

-- ============================================================
-- TABLE 1: USERS
-- Core authentication and identity table
-- ============================================================
CREATE TABLE users (
    user_id     SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE 2: RISK_PROFILES  (seeded data)
-- Predefined risk categories with score ranges
-- ============================================================
CREATE TABLE risk_profiles (
    risk_profile_id SERIAL PRIMARY KEY,
    profile_name    VARCHAR(50) NOT NULL,
    min_score       INT NOT NULL,
    max_score       INT NOT NULL,
    description     TEXT,
    CONSTRAINT chk_score_range CHECK (min_score >= 0 AND max_score <= 100 AND min_score < max_score)
);

-- ============================================================
-- TABLE 3: USER_PROFILES
-- Financial details, goals, and computed risk score
-- ============================================================
CREATE TABLE user_profiles (
    profile_id              SERIAL PRIMARY KEY,
    user_id                 INT UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    monthly_income          NUMERIC(12,2),
    monthly_expenses        NUMERIC(12,2),
    investment_amount       NUMERIC(12,2),
    investment_horizon_years INT,
    investment_goal         VARCHAR(100),
    risk_score              INT,
    risk_profile_id         INT REFERENCES risk_profiles(risk_profile_id),
    updated_at              TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_income    CHECK (monthly_income >= 0),
    CONSTRAINT chk_expenses  CHECK (monthly_expenses >= 0),
    CONSTRAINT chk_investment CHECK (investment_amount > 0),
    CONSTRAINT chk_horizon   CHECK (investment_horizon_years > 0),
    CONSTRAINT chk_risk_score CHECK (risk_score BETWEEN 0 AND 100)
);

-- ============================================================
-- TABLE 4: ASSET_CLASSES  (seeded data)
-- Equity, Debt, Gold, Cash, International, Real Estate
-- ============================================================
CREATE TABLE asset_classes (
    asset_class_id SERIAL PRIMARY KEY,
    name           VARCHAR(100) NOT NULL,
    description    TEXT
);

-- ============================================================
-- TABLE 5: PORTFOLIO_MODELS  (seeded data)
-- Named model templates linked to risk profiles
-- ============================================================
CREATE TABLE portfolio_models (
    model_id        SERIAL PRIMARY KEY,
    model_name      VARCHAR(100) NOT NULL,
    risk_profile_id INT REFERENCES risk_profiles(risk_profile_id),
    description     TEXT
);

-- ============================================================
-- TABLE 6: PORTFOLIO_ALLOCATIONS  (seeded data)
-- Top-level % split of asset classes per model
-- ============================================================
CREATE TABLE portfolio_allocations (
    allocation_id         SERIAL PRIMARY KEY,
    model_id              INT REFERENCES portfolio_models(model_id) ON DELETE CASCADE,
    asset_class_id        INT REFERENCES asset_classes(asset_class_id),
    allocation_percentage NUMERIC(5,2) NOT NULL,
    CONSTRAINT chk_pa_pct CHECK (allocation_percentage > 0 AND allocation_percentage <= 100)
);

-- ============================================================
-- TABLE 7: SUB_ALLOCATION_TEMPLATES  (seeded data)
-- Bridge between a model and its instrument groups per asset class
-- ============================================================
CREATE TABLE sub_allocation_templates (
    template_id    SERIAL PRIMARY KEY,
    model_id       INT REFERENCES portfolio_models(model_id) ON DELETE CASCADE,
    asset_class_id INT REFERENCES asset_classes(asset_class_id)
);

-- ============================================================
-- TABLE 8: INSTRUMENTS  (seeded data)
-- Actual financial instruments (ETFs, mutual funds, bonds)
-- ============================================================
CREATE TABLE instruments (
    instrument_id   SERIAL PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    ticker          VARCHAR(30),
    asset_class_id  INT REFERENCES asset_classes(asset_class_id),
    instrument_type VARCHAR(50),
    fund_house      VARCHAR(100),
    is_active       BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- TABLE 9: INSTRUMENT_ALLOCATIONS  (seeded data)
-- % of each instrument within a sub-allocation template
-- ============================================================
CREATE TABLE instrument_allocations (
    inst_allocation_id    SERIAL PRIMARY KEY,
    template_id           INT REFERENCES sub_allocation_templates(template_id) ON DELETE CASCADE,
    instrument_id         INT REFERENCES instruments(instrument_id),
    allocation_percentage NUMERIC(5,2) NOT NULL,
    CONSTRAINT chk_ia_pct CHECK (allocation_percentage > 0 AND allocation_percentage <= 100)
);

-- ============================================================
-- TABLE 10: USER_PORTFOLIOS
-- A generated portfolio instance per user
-- ============================================================
CREATE TABLE user_portfolios (
    portfolio_id      SERIAL PRIMARY KEY,
    user_id           INT REFERENCES users(user_id) ON DELETE CASCADE,
    model_id          INT REFERENCES portfolio_models(model_id),
    total_investment  NUMERIC(14,2) NOT NULL,
    is_active         BOOLEAN DEFAULT TRUE,
    version           INT DEFAULT 1,
    generated_at      TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_investment_amt CHECK (total_investment > 0),
    CONSTRAINT chk_version CHECK (version >= 1)
);

-- ============================================================
-- TABLE 11: USER_PORTFOLIO_POSITIONS
-- Individual instrument positions in a portfolio
-- ============================================================
CREATE TABLE user_portfolio_positions (
    position_id           SERIAL PRIMARY KEY,
    portfolio_id          INT REFERENCES user_portfolios(portfolio_id) ON DELETE CASCADE,
    instrument_id         INT REFERENCES instruments(instrument_id),
    allocation_percentage NUMERIC(5,2),
    allocated_amount      NUMERIC(14,2),
    CONSTRAINT chk_pos_pct    CHECK (allocation_percentage > 0 AND allocation_percentage <= 100),
    CONSTRAINT chk_pos_amount CHECK (allocated_amount > 0)
);

-- ============================================================
-- TABLE 12: INSTRUMENT_RETURNS  (seeded mock data)
-- Historical return data (1Y / 3Y / 5Y) per instrument
-- ============================================================
CREATE TABLE instrument_returns (
    return_id         SERIAL PRIMARY KEY,
    instrument_id     INT REFERENCES instruments(instrument_id) ON DELETE CASCADE,
    period            VARCHAR(10) NOT NULL,
    return_percentage NUMERIC(6,2),
    recorded_at       DATE DEFAULT CURRENT_DATE,
    CONSTRAINT chk_period CHECK (period IN ('1Y', '3Y', '5Y'))
);

-- ============================================================
-- TABLE 13: AUDIT_LOG  (auto-populated by trigger)
-- Auto-populated log of key user actions
-- ============================================================
CREATE TABLE audit_log (
    log_id     SERIAL PRIMARY KEY,
    user_id    INT REFERENCES users(user_id),
    action     VARCHAR(100) NOT NULL,
    metadata   JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_user_profiles_user_id      ON user_profiles(user_id);
CREATE INDEX idx_user_portfolios_user_id    ON user_portfolios(user_id);
CREATE INDEX idx_user_portfolios_active     ON user_portfolios(user_id, is_active);
CREATE INDEX idx_portfolio_alloc_model_id   ON portfolio_allocations(model_id);
CREATE INDEX idx_sub_alloc_model_id         ON sub_allocation_templates(model_id);
CREATE INDEX idx_inst_alloc_template_id     ON instrument_allocations(template_id);
CREATE INDEX idx_positions_portfolio_id     ON user_portfolio_positions(portfolio_id);
CREATE INDEX idx_instrument_returns_inst_id ON instrument_returns(instrument_id);
CREATE INDEX idx_audit_log_user_id          ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at       ON audit_log(created_at);
CREATE INDEX idx_instruments_asset_class    ON instruments(asset_class_id);

-- ============================================================
-- Validation function: check allocation sums per model
-- Run after seeding to verify data integrity
-- ============================================================
CREATE OR REPLACE FUNCTION validate_allocation_sums()
RETURNS TABLE(check_name TEXT, model_id INT, total NUMERIC, is_valid BOOLEAN) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'portfolio_allocations' AS check_name,
        pa.model_id,
        SUM(pa.allocation_percentage) AS total,
        ABS(SUM(pa.allocation_percentage) - 100) < 0.01 AS is_valid
    FROM portfolio_allocations pa
    GROUP BY pa.model_id

    UNION ALL

    SELECT
        'instrument_allocations' AS check_name,
        sat.model_id,
        SUM(ia.allocation_percentage) AS total,
        ABS(SUM(ia.allocation_percentage) - 100) < 0.01 AS is_valid
    FROM instrument_allocations ia
    JOIN sub_allocation_templates sat ON sat.template_id = ia.template_id
    GROUP BY sat.model_id, sat.template_id;
END;
$$ LANGUAGE plpgsql;
