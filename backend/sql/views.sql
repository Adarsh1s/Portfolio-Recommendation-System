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
