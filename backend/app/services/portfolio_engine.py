"""
Portfolio Generation Engine
----------------------------
Executes the complete portfolio generation transaction:
  1. Deactivate previous active portfolio for user
  2. Insert new user_portfolio row (trigger auto-fires audit log)
  3. Bulk-insert all instrument positions via multi-table join
  4. Return fully hydrated portfolio response

Uses raw asyncpg for the complex INSERT..SELECT to showcase DBMS capabilities.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.schemas.schemas import PortfolioOut, PortfolioPositionOut
from fastapi import HTTPException


async def generate_portfolio(
    db: AsyncSession,
    user_id: int,
) -> PortfolioOut:
    """
    Full transactional portfolio generation.
    If any step fails the whole transaction rolls back.
    """
    async with db.begin():
        # ── Step 1: Verify user profile + get investment amount ──────────
        profile_result = await db.execute(
            text("SELECT risk_profile_id, investment_amount FROM user_profiles WHERE user_id = :uid"),
            {"uid": user_id},
        )
        profile = profile_result.fetchone()
        if not profile or not profile.risk_profile_id:
            raise HTTPException(
                status_code=400,
                detail="Complete onboarding and risk questionnaire before generating a portfolio.",
            )
        investment_amount = float(profile.investment_amount)

        # ── Step 2: Get model_id via stored function ──────────────────────
        model_result = await db.execute(
            text("SELECT get_portfolio_model_for_user(:user_id)"),
            {"user_id": user_id},
        )
        model_id = model_result.scalar()
        if not model_id:
            raise HTTPException(status_code=400, detail="No portfolio model found. Complete your profile and questionnaire first.")

        # ── Step 2: Deactivate old portfolios ─────────────────────────────
        await db.execute(
            text("""
                UPDATE user_portfolios
                SET is_active = FALSE
                WHERE user_id = :user_id AND is_active = TRUE
            """),
            {"user_id": user_id},
        )

        # ── Step 3: Calculate next version number ─────────────────────────
        version_result = await db.execute(
            text("""
                SELECT COALESCE(MAX(version), 0) + 1
                FROM user_portfolios
                WHERE user_id = :user_id
            """),
            {"user_id": user_id},
        )
        next_version = version_result.scalar()

        # ── Step 4: Insert new portfolio (trigger fires here) ─────────────
        portfolio_result = await db.execute(
            text("""
                INSERT INTO user_portfolios
                    (user_id, model_id, total_investment, is_active, version)
                VALUES
                    (:user_id, :model_id, :total_investment, TRUE, :version)
                RETURNING portfolio_id, generated_at
            """),
            {
                "user_id":          user_id,
                "model_id":         model_id,
                "total_investment": investment_amount,
                "version":          next_version,
            },
        )
        row = portfolio_result.fetchone()
        portfolio_id = row.portfolio_id
        generated_at = row.generated_at

        # ── Step 5: Bulk-insert all positions via multi-table join ────────
        await db.execute(
            text("""
                INSERT INTO user_portfolio_positions
                    (portfolio_id, instrument_id, allocation_percentage, allocated_amount)
                SELECT
                    :portfolio_id,
                    ia.instrument_id,
                    ROUND((pa.allocation_percentage * ia.allocation_percentage / 100.0), 4),
                    ROUND((:total_investment * pa.allocation_percentage * ia.allocation_percentage / 10000.0), 2)
                FROM portfolio_allocations pa
                JOIN sub_allocation_templates sat
                    ON sat.model_id = pa.model_id
                    AND sat.asset_class_id = pa.asset_class_id
                JOIN instrument_allocations ia
                    ON ia.template_id = sat.template_id
                WHERE pa.model_id = :model_id
            """),
            {
                "portfolio_id":     portfolio_id,
                "total_investment": investment_amount,
                "model_id":         model_id,
            },
        )

    # ── Step 6: Fetch hydrated portfolio for response ─────────────────────
    return await get_portfolio_by_id(db, portfolio_id, user_id)


async def get_portfolio_by_id(
    db: AsyncSession,
    portfolio_id: int,
    user_id: int,
) -> PortfolioOut:
    result = await db.execute(
        text("""
            SELECT
                up.portfolio_id, up.user_id, up.total_investment,
                up.is_active, up.version, up.generated_at,
                pm.model_name, rp.profile_name AS risk_profile,
                upp.position_id, upp.instrument_id,
                i.name AS instrument_name, i.ticker, i.instrument_type, i.fund_house,
                ac.name AS asset_class,
                upp.allocation_percentage, upp.allocated_amount
            FROM user_portfolios up
            JOIN portfolio_models pm   ON pm.model_id      = up.model_id
            JOIN risk_profiles rp      ON rp.risk_profile_id = pm.risk_profile_id
            JOIN user_portfolio_positions upp ON upp.portfolio_id = up.portfolio_id
            JOIN instruments i         ON i.instrument_id  = upp.instrument_id
            JOIN asset_classes ac      ON ac.asset_class_id = i.asset_class_id
            WHERE up.portfolio_id = :portfolio_id AND up.user_id = :user_id
            ORDER BY ac.name, upp.allocation_percentage DESC
        """),
        {"portfolio_id": portfolio_id, "user_id": user_id},
    )
    rows = result.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    first = rows[0]
    positions = [
        PortfolioPositionOut(
            position_id=r.position_id,
            instrument_id=r.instrument_id,
            instrument_name=r.instrument_name,
            ticker=r.ticker,
            instrument_type=r.instrument_type,
            fund_house=r.fund_house,
            asset_class=r.asset_class,
            allocation_percentage=float(r.allocation_percentage),
            allocated_amount=float(r.allocated_amount),
        )
        for r in rows
    ]

    return PortfolioOut(
        portfolio_id=first.portfolio_id,
        user_id=first.user_id,
        model_name=first.model_name,
        risk_profile=first.risk_profile,
        total_investment=float(first.total_investment),
        is_active=first.is_active,
        version=first.version,
        generated_at=first.generated_at,
        positions=positions,
    )


async def get_active_portfolio(db: AsyncSession, user_id: int) -> PortfolioOut:
    result = await db.execute(
        text("""
            SELECT portfolio_id FROM user_portfolios
            WHERE user_id = :user_id AND is_active = TRUE
            LIMIT 1
        """),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No active portfolio found. Generate one first.")
    return await get_portfolio_by_id(db, row.portfolio_id, user_id)
