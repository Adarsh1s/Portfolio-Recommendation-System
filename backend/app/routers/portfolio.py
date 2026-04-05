from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.schemas import (
    PortfolioOut, AssetClassSummaryOut, ExpectedReturnsOut, PortfolioCompareOut
)
from app.services.portfolio_engine import generate_portfolio, get_active_portfolio

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.post("/generate", response_model=PortfolioOut, status_code=201)
async def generate(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new portfolio for the user.
    Requires completed profile + questionnaire.
    Deactivates previous portfolio and creates a new versioned one.
    """
    # Delegate profile verification and portfolio generation to the service
    return await generate_portfolio(db, user_id)


@router.get("/current", response_model=PortfolioOut)
async def get_current_portfolio(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_active_portfolio(db, user_id)


@router.get("/history")
async def get_history(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """All portfolio versions for the user, newest first."""
    result = await db.execute(
        text("""
            SELECT up.portfolio_id, up.version, up.total_investment, up.is_active,
                   up.generated_at, pm.model_name, rp.profile_name
            FROM user_portfolios up
            JOIN portfolio_models pm ON pm.model_id = up.model_id
            JOIN risk_profiles rp    ON rp.risk_profile_id = pm.risk_profile_id
            WHERE up.user_id = :uid
            ORDER BY up.version DESC
        """),
        {"uid": user_id},
    )
    rows = result.fetchall()
    return [
        {
            "portfolio_id":     r.portfolio_id,
            "version":          r.version,
            "total_investment":  float(r.total_investment),
            "is_active":        r.is_active,
            "generated_at":     r.generated_at,
            "model_name":       r.model_name,
            "risk_profile":     r.profile_name,
        }
        for r in rows
    ]


@router.get("/summary", response_model=list[AssetClassSummaryOut])
async def get_summary(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Asset-class level breakdown of the active portfolio."""
    result = await db.execute(
        text("""
            SELECT asset_class, total_allocation_pct, total_allocated_amount
            FROM asset_class_summary
            WHERE user_id = :uid AND is_active = TRUE
            ORDER BY total_allocation_pct DESC
        """),
        {"uid": user_id},
    )
    rows = result.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="No active portfolio found")
    return [
        AssetClassSummaryOut(
            asset_class=r.asset_class,
            total_allocation_pct=float(r.total_allocation_pct),
            total_allocated_amount=float(r.total_allocated_amount),
        )
        for r in rows
    ]


@router.get("/expected-returns", response_model=ExpectedReturnsOut)
async def get_expected_returns(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Blended weighted 1Y/3Y/5Y return estimate using the DB function."""
    # Get active portfolio_id
    pid_result = await db.execute(
        text("SELECT portfolio_id FROM user_portfolios WHERE user_id = :uid AND is_active = TRUE"),
        {"uid": user_id},
    )
    pid_row = pid_result.fetchone()
    if not pid_row:
        raise HTTPException(status_code=404, detail="No active portfolio found")

    result = await db.execute(
        text("SELECT * FROM calculate_expected_returns(:pid)"),
        {"pid": pid_row.portfolio_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Could not calculate returns")

    return ExpectedReturnsOut(
        weighted_return_1y=float(row.weighted_return_1y or 0),
        weighted_return_3y=float(row.weighted_return_3y or 0),
        weighted_return_5y=float(row.weighted_return_5y or 0),
    )


@router.get("/compare/{risk_level}", response_model=PortfolioCompareOut)
async def compare_portfolios(
    risk_level: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare user's active portfolio asset allocation
    against any other risk profile model.
    risk_level: conservative | moderately_conservative | moderate | aggressive
    """
    level_map = {
        "conservative":           1,
        "moderately_conservative": 2,
        "moderate":               3,
        "aggressive":             4,
    }
    profile_id = level_map.get(risk_level.lower())
    if not profile_id:
        raise HTTPException(status_code=400, detail=f"Invalid risk_level. Choose from: {list(level_map)}")

    # Current portfolio asset breakdown
    current = await db.execute(
        text("""
            SELECT asset_class, total_allocation_pct, total_allocated_amount
            FROM asset_class_summary
            WHERE user_id = :uid AND is_active = TRUE
            ORDER BY total_allocation_pct DESC
        """),
        {"uid": user_id},
    )
    current_rows = current.fetchall()
    if not current_rows:
        raise HTTPException(status_code=404, detail="No active portfolio to compare")

    # Compared model allocations (from view)
    compared = await db.execute(
        text("""
            SELECT pmo.model_name, pmo.asset_class, pmo.allocation_percentage
            FROM portfolio_model_overview pmo
            JOIN portfolio_models pm ON pm.model_id = pmo.model_id
            WHERE pm.risk_profile_id = :pid
            ORDER BY pmo.allocation_percentage DESC
        """),
        {"pid": profile_id},
    )
    compared_rows = compared.fetchall()
    model_name = compared_rows[0].model_name if compared_rows else "Unknown"

    return PortfolioCompareOut(
        current_portfolio=[
            AssetClassSummaryOut(
                asset_class=r.asset_class,
                total_allocation_pct=float(r.total_allocation_pct),
                total_allocated_amount=float(r.total_allocated_amount),
            )
            for r in current_rows
        ],
        compared_model_name=model_name,
        compared_allocations=[
            {"asset_class": r.asset_class, "allocation_percentage": float(r.allocation_percentage)}
            for r in compared_rows
        ],
    )
