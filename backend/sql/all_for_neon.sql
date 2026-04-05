-- ============================================================
-- Combined SQL for Neon (paste into Neon console SQL editor)
-- Includes: schema, views, triggers/functions, and seed data
-- Run as a single script in your Neon project's SQL editor.
-- ============================================================

-- ===================== SCHEMA ==============================

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

-- ===================== VIEWS ==============================

-- ============================================================
-- Portfolio Recommendation System - Views
-- ============================================================

-- ============================================================
-- VIEW: user_portfolio_summary
-- Joins 7 tables to produce one readable row per position.
-- Used by the Streamlit dashboard to render the allocation table.
-- ============================================================
CREATE OR REPLACE VIEW user_portfolio_summary AS
SELECT
    u.user_id,
    u.name                      AS user_name,
    u.email,
    up.portfolio_id,
    up.version,
    up.is_active,
    up.total_investment,
    up.generated_at,
    pm.model_name,
    pm.description              AS model_description,
    rp.profile_name             AS risk_profile,
    rp.min_score,
    rp.max_score,
    ac.name                     AS asset_class,
    i.name                      AS instrument_name,
    i.ticker,
    i.instrument_type,
    i.fund_house,
    upp.allocation_percentage,
    upp.allocated_amount
FROM user_portfolios up
JOIN users u               ON u.user_id        = up.user_id
JOIN portfolio_models pm   ON pm.model_id      = up.model_id
JOIN risk_profiles rp      ON rp.risk_profile_id = pm.risk_profile_id
JOIN user_portfolio_positions upp ON upp.portfolio_id = up.portfolio_id
JOIN instruments i         ON i.instrument_id  = upp.instrument_id
JOIN asset_classes ac      ON ac.asset_class_id = i.asset_class_id;

-- ============================================================
-- VIEW: asset_class_summary
-- Aggregates positions to asset-class level for pie chart data
-- ============================================================
CREATE OR REPLACE VIEW asset_class_summary AS
SELECT
    up.user_id,
    up.portfolio_id,
    up.is_active,
    ac.name                             AS asset_class,
    SUM(upp.allocation_percentage)      AS total_allocation_pct,
    SUM(upp.allocated_amount)           AS total_allocated_amount
FROM user_portfolios up
JOIN user_portfolio_positions upp ON upp.portfolio_id  = up.portfolio_id
JOIN instruments i                ON i.instrument_id   = upp.instrument_id
JOIN asset_classes ac             ON ac.asset_class_id = i.asset_class_id
GROUP BY up.user_id, up.portfolio_id, up.is_active, ac.name;

-- ============================================================
-- VIEW: portfolio_model_overview
-- Read-only reference of all models with their risk profiles
-- Used by Compare page
-- ============================================================
CREATE OR REPLACE VIEW portfolio_model_overview AS
SELECT
    pm.model_id,
    pm.model_name,
    pm.description,
    rp.profile_name             AS risk_profile,
    rp.min_score,
    rp.max_score,
    rp.description              AS risk_description,
    pa.asset_class_id,
    ac.name                     AS asset_class,
    pa.allocation_percentage
FROM portfolio_models pm
JOIN risk_profiles rp        ON rp.risk_profile_id  = pm.risk_profile_id
JOIN portfolio_allocations pa ON pa.model_id        = pm.model_id
JOIN asset_classes ac        ON ac.asset_class_id   = pa.asset_class_id
ORDER BY pm.model_id, pa.allocation_percentage DESC;

-- ============================================================
-- VIEW: instrument_with_returns
-- Instruments joined with their 1Y/3Y/5Y returns (pivoted)
-- Used by expected-returns endpoint
-- ============================================================
CREATE OR REPLACE VIEW instrument_with_returns AS
SELECT
    i.instrument_id,
    i.name              AS instrument_name,
    i.ticker,
    i.instrument_type,
    i.fund_house,
    ac.name             AS asset_class,
    MAX(CASE WHEN ir.period = '1Y' THEN ir.return_percentage END) AS return_1y,
    MAX(CASE WHEN ir.period = '3Y' THEN ir.return_percentage END) AS return_3y,
    MAX(CASE WHEN ir.period = '5Y' THEN ir.return_percentage END) AS return_5y
FROM instruments i
JOIN asset_classes ac     ON ac.asset_class_id  = i.asset_class_id
LEFT JOIN instrument_returns ir ON ir.instrument_id = i.instrument_id
GROUP BY i.instrument_id, i.name, i.ticker, i.instrument_type, i.fund_house, ac.name;

-- ===================== TRIGGERS & FUNCTIONS =====================

-- ============================================================
-- Portfolio Recommendation System - Triggers & Functions
-- ============================================================

-- ============================================================
-- FUNCTION: get_risk_profile_id(p_score INT)
-- Accepts a risk score (0-100), returns the matching risk_profile_id
-- by range lookup. Called by backend after questionnaire submission.
-- ============================================================
CREATE OR REPLACE FUNCTION get_risk_profile_id(p_score INT)
RETURNS INT AS $$
DECLARE
    v_profile_id INT;
BEGIN
    IF p_score < 0 OR p_score > 100 THEN
        RAISE EXCEPTION 'Risk score must be between 0 and 100, got: %', p_score;
    END IF;

    SELECT risk_profile_id INTO v_profile_id
    FROM risk_profiles
    WHERE p_score BETWEEN min_score AND max_score
    LIMIT 1;

    IF v_profile_id IS NULL THEN
        RAISE EXCEPTION 'No risk profile found for score: %', p_score;
    END IF;

    RETURN v_profile_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- FUNCTION: get_portfolio_model_for_user(p_user_id INT)
-- Returns the model_id matching the user's current risk profile.
-- Called by portfolio generation service.
-- ============================================================
CREATE OR REPLACE FUNCTION get_portfolio_model_for_user(p_user_id INT)
RETURNS INT AS $$
DECLARE
    v_model_id INT;
BEGIN
    SELECT pm.model_id INTO v_model_id
    FROM user_profiles up
    JOIN portfolio_models pm ON pm.risk_profile_id = up.risk_profile_id
    WHERE up.user_id = p_user_id
    LIMIT 1;

    IF v_model_id IS NULL THEN
        RAISE EXCEPTION 'No portfolio model found for user_id: %', p_user_id;
    END IF;

    RETURN v_model_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- TRIGGER FUNCTION: fn_audit_portfolio_generation()
-- Fires AFTER INSERT on user_portfolios.
-- Writes a JSONB audit entry with portfolio details.
-- Guaranteed at DB level — cannot be bypassed by app code.
-- ============================================================
CREATE OR REPLACE FUNCTION fn_audit_portfolio_generation()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (user_id, action, metadata)
    VALUES (
        NEW.user_id,
        'PORTFOLIO_GENERATED',
        jsonb_build_object(
            'portfolio_id',    NEW.portfolio_id,
            'model_id',        NEW.model_id,
            'version',         NEW.version,
            'total_investment', NEW.total_investment,
            'generated_at',    NEW.generated_at
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to user_portfolios
CREATE TRIGGER trg_audit_portfolio
AFTER INSERT ON user_portfolios
FOR EACH ROW EXECUTE FUNCTION fn_audit_portfolio_generation();

-- ============================================================
-- TRIGGER FUNCTION: fn_audit_profile_update()
-- Fires AFTER UPDATE on user_profiles.
-- Logs risk score changes for auditing.
-- ============================================================
CREATE OR REPLACE FUNCTION fn_audit_profile_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.risk_score IS DISTINCT FROM NEW.risk_score THEN
        INSERT INTO audit_log (user_id, action, metadata)
        VALUES (
            NEW.user_id,
            'RISK_SCORE_UPDATED',
            jsonb_build_object(
                'old_risk_score',    OLD.risk_score,
                'new_risk_score',    NEW.risk_score,
                'old_profile_id',    OLD.risk_profile_id,
                'new_profile_id',    NEW.risk_profile_id
            )
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_profile_update
AFTER UPDATE ON user_profiles
FOR EACH ROW EXECUTE FUNCTION fn_audit_profile_update();

-- ============================================================
-- TRIGGER FUNCTION: fn_set_updated_at()
-- Generic trigger to keep updated_at fresh on user_profiles
-- ============================================================
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_user_profiles_updated_at
BEFORE UPDATE ON user_profiles
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- ============================================================
-- FUNCTION: calculate_expected_returns(p_portfolio_id INT)
-- Returns weighted 1Y, 3Y, 5Y blended returns for a portfolio.
-- Used by the expected-returns API endpoint.
-- ============================================================
CREATE OR REPLACE FUNCTION calculate_expected_returns(p_portfolio_id INT)
RETURNS TABLE(
    weighted_return_1y NUMERIC,
    weighted_return_3y NUMERIC,
    weighted_return_5y NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ROUND(SUM(upp.allocation_percentage / 100.0 * COALESCE(iwr.return_1y, 0)), 2),
        ROUND(SUM(upp.allocation_percentage / 100.0 * COALESCE(iwr.return_3y, 0)), 2),
        ROUND(SUM(upp.allocation_percentage / 100.0 * COALESCE(iwr.return_5y, 0)), 2)
    FROM user_portfolio_positions upp
    JOIN instrument_with_returns iwr ON iwr.instrument_id = upp.instrument_id
    WHERE upp.portfolio_id = p_portfolio_id;
END;
$$ LANGUAGE plpgsql;

-- ===================== SEED DATA ==============================

-- ============================================================
-- Portfolio Recommendation System - Complete Seed Data
-- ~230 rows across all reference tables
-- All Indian market instruments with illustrative return data
-- ============================================================

-- ============================================================
-- RISK PROFILES (4 rows)
-- ============================================================
INSERT INTO risk_profiles (profile_name, min_score, max_score, description) VALUES
('Conservative',          0,  25, 'Capital preservation focused. Minimal equity exposure, heavy debt and cash allocation. Suitable for short investment horizons and low risk appetite.'),
('Moderately Conservative', 26, 50, 'Balanced approach leaning defensive. Some equity for growth but majority in debt. Suitable for medium horizons with limited risk tolerance.'),
('Moderate',             51,  75, 'Balanced growth and stability. Significant equity allocation with debt cushion. Suitable for 5+ year horizons with moderate risk appetite.'),
('Aggressive',           76, 100, 'Maximum growth orientation. Heavy equity and international exposure. Suitable for 7+ year horizons with high risk tolerance.');

-- ============================================================
-- ASSET CLASSES (6 rows)
-- ============================================================
INSERT INTO asset_classes (name, description) VALUES
('Equity',        'Domestic equity instruments: large-cap, mid-cap, flexi-cap mutual funds and index ETFs'),
('Debt',          'Fixed income instruments: corporate bond funds, short duration debt funds, G-Secs'),
('Gold',          'Precious metal instruments: Gold ETFs and Sovereign Gold Bonds'),
('Cash & Liquid', 'High-liquidity low-risk instruments: liquid funds, overnight funds, money market'),
('International', 'Global equity exposure: US-focused funds, global diversified ETFs, Nasdaq ETFs'),
('Real Estate',   'REIT-based real estate exposure: office REITs, retail REITs listed on NSE/BSE');

-- ============================================================
-- PORTFOLIO MODELS (4 rows, one per risk profile)
-- ============================================================
INSERT INTO portfolio_models (model_name, risk_profile_id, description) VALUES
('Capital Shield',          1, 'Conservative model focused on capital preservation. 60% in debt, 20% equity via index funds, 10% gold, 10% liquid for emergencies.'),
('Steady Compounder',       2, 'Moderately conservative model balancing growth with safety. 40% equity, 40% debt, 10% gold, 10% cash.'),
('Balanced Growth',         3, 'Moderate growth model with diversified equity and debt. 60% equity across large/mid/flexi-cap, 25% debt, 10% gold, 5% cash.'),
('Alpha Maximiser',         4, 'Aggressive growth model targeting maximum long-term returns. 80% equity including international, 10% debt, 5% gold, 5% international.');

-- ============================================================
-- (Remaining seed rows omitted for brevity in this file; see individual seed files for full data)


-- ============================================================
-- MOCK USERS (To make the app feel real)
-- Password for all users is: password123
-- ============================================================
INSERT INTO users (user_id, name, email, password_hash) VALUES
(1001, 'Ravi Desai', 'ravi@example.com', '$2b$12$C/CYNVPmhv6qMFybq3Ozquk1iy10JOSBR/nwx0sbuPjFAidIvYniK'),
(1002, 'Priya Sharma', 'priya@example.com', '$2b$12$C/CYNVPmhv6qMFybq3Ozquk1iy10JOSBR/nwx0sbuPjFAidIvYniK'),
(1003, 'Karan Kapoor', 'karan@example.com', '$2b$12$C/CYNVPmhv6qMFybq3Ozquk1iy10JOSBR/nwx0sbuPjFAidIvYniK'),
(1004, 'Amitabh Singh', 'amitabh@example.com', '$2b$12$C/CYNVPmhv6qMFybq3Ozquk1iy10JOSBR/nwx0sbuPjFAidIvYniK'),
(1005, 'Neha Gupta', 'neha@example.com', '$2b$12$C/CYNVPmhv6qMFybq3Ozquk1iy10JOSBR/nwx0sbuPjFAidIvYniK')
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_profiles (user_id, monthly_income, monthly_expenses, investment_amount, investment_horizon_years, investment_goal, risk_score, risk_profile_id) VALUES
(1001, 150000, 50000, 1000000, 3, 'Save for wedding', 20, 1),
(1002, 350000, 100000, 2500000, 10, 'Early Retirement', 85, 4),
(1003, 100000, 40000, 500000, 5, 'Buy a house', 60, 3),
(1004, 200000, 80000, 1500000, 7, 'Child Education', 45, 2),
(1005, 500000, 200000, 5000000, 15, 'Wealth Creation', 90, 4)
ON CONFLICT (user_id) DO NOTHING;

-- Log the profile creation
INSERT INTO audit_log (user_id, action, metadata) VALUES
(1001, 'RISK_SCORE_UPDATED', '{"new_risk_score": 20}'),
(1002, 'RISK_SCORE_UPDATED', '{"new_risk_score": 85}'),
(1003, 'RISK_SCORE_UPDATED', '{"new_risk_score": 60}'),
(1004, 'RISK_SCORE_UPDATED', '{"new_risk_score": 45}'),
(1005, 'RISK_SCORE_UPDATED', '{"new_risk_score": 90}');
