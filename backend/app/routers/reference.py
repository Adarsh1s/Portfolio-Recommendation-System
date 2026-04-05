from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.schemas import InstrumentOut, RiskProfileOut, PortfolioModelOut

router = APIRouter(tags=["Reference Data"])


@router.get("/instruments", response_model=list[InstrumentOut])
async def list_instruments(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT
                i.instrument_id, i.name, i.ticker, ac.name AS asset_class,
                i.instrument_type, i.fund_house,
                iwr.return_1y, iwr.return_3y, iwr.return_5y
            FROM instruments i
            JOIN asset_classes ac ON ac.asset_class_id = i.asset_class_id
            LEFT JOIN instrument_with_returns iwr ON iwr.instrument_id = i.instrument_id
            WHERE i.is_active = TRUE
            ORDER BY ac.name, i.name
        """)
    )
    rows = result.fetchall()
    return [
        InstrumentOut(
            instrument_id=r.instrument_id,
            name=r.name,
            ticker=r.ticker,
            asset_class=r.asset_class,
            instrument_type=r.instrument_type,
            fund_house=r.fund_house,
            return_1y=float(r.return_1y) if r.return_1y else None,
            return_3y=float(r.return_3y) if r.return_3y else None,
            return_5y=float(r.return_5y) if r.return_5y else None,
        )
        for r in rows
    ]


@router.get("/risk-profiles", response_model=list[RiskProfileOut])
async def list_risk_profiles(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT * FROM risk_profiles ORDER BY min_score")
    )
    rows = result.fetchall()
    return [
        RiskProfileOut(
            risk_profile_id=r.risk_profile_id,
            profile_name=r.profile_name,
            min_score=r.min_score,
            max_score=r.max_score,
            description=r.description,
        )
        for r in rows
    ]


@router.get("/portfolio-models", response_model=list[PortfolioModelOut])
async def list_portfolio_models(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT pm.model_id, pm.model_name, pm.risk_profile_id,
                   rp.profile_name AS risk_profile, pm.description
            FROM portfolio_models pm
            JOIN risk_profiles rp ON rp.risk_profile_id = pm.risk_profile_id
            ORDER BY pm.model_id
        """)
    )
    rows = result.fetchall()
    return [
        PortfolioModelOut(
            model_id=r.model_id,
            model_name=r.model_name,
            risk_profile_id=r.risk_profile_id,
            risk_profile=r.risk_profile,
            description=r.description,
        )
        for r in rows
    ]
