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
