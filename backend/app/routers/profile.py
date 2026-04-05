from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.schemas import ProfileCreate, ProfileUpdate, ProfileOut

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post("/create", response_model=ProfileOut, status_code=201)
async def create_profile(
    payload: ProfileCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Check if profile already exists
    existing = await db.execute(
        text("SELECT profile_id FROM user_profiles WHERE user_id = :uid"),
        {"uid": user_id},
    )
    if existing.fetchone():
        raise HTTPException(status_code=409, detail="Profile already exists. Use PUT /profile/update")

    result = await db.execute(
        text("""
            INSERT INTO user_profiles
                (user_id, monthly_income, monthly_expenses, investment_amount,
                 investment_horizon_years, investment_goal)
            VALUES
                (:user_id, :income, :expenses, :investment, :horizon, :goal)
            RETURNING profile_id, user_id, monthly_income, monthly_expenses,
                      investment_amount, investment_horizon_years, investment_goal,
                      risk_score, risk_profile_id, updated_at
        """),
        {
            "user_id":    user_id,
            "income":     payload.monthly_income,
            "expenses":   payload.monthly_expenses,
            "investment": payload.investment_amount,
            "horizon":    payload.investment_horizon_years,
            "goal":       payload.investment_goal,
        },
    )
    await db.commit()
    row = result.fetchone()
    return _row_to_profile_out(row, risk_profile_name=None)


@router.put("/update", response_model=ProfileOut)
async def update_profile(
    payload: ProfileUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            UPDATE user_profiles
            SET monthly_income           = :income,
                monthly_expenses         = :expenses,
                investment_amount        = :investment,
                investment_horizon_years = :horizon,
                investment_goal          = :goal,
                risk_score               = NULL,
                risk_profile_id          = NULL
            WHERE user_id = :user_id
            RETURNING profile_id, user_id, monthly_income, monthly_expenses,
                      investment_amount, investment_horizon_years, investment_goal,
                      risk_score, risk_profile_id, updated_at
        """),
        {
            "user_id":    user_id,
            "income":     payload.monthly_income,
            "expenses":   payload.monthly_expenses,
            "investment": payload.investment_amount,
            "horizon":    payload.investment_horizon_years,
            "goal":       payload.investment_goal,
        },
    )
    await db.commit()
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found. Create it first.")
    return _row_to_profile_out(row, risk_profile_name=None)


@router.get("/me", response_model=ProfileOut)
async def get_my_profile(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT up.profile_id, up.user_id, up.monthly_income, up.monthly_expenses,
                   up.investment_amount, up.investment_horizon_years, up.investment_goal,
                   up.risk_score, up.risk_profile_id, up.updated_at,
                   rp.profile_name AS risk_profile_name
            FROM user_profiles up
            LEFT JOIN risk_profiles rp ON rp.risk_profile_id = up.risk_profile_id
            WHERE up.user_id = :uid
        """),
        {"uid": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _row_to_profile_out(row, risk_profile_name=getattr(row, "risk_profile_name", None))


def _row_to_profile_out(row, risk_profile_name: str | None) -> ProfileOut:
    return ProfileOut(
        profile_id=row.profile_id,
        user_id=row.user_id,
        monthly_income=float(row.monthly_income),
        monthly_expenses=float(row.monthly_expenses),
        investment_amount=float(row.investment_amount),
        investment_horizon_years=row.investment_horizon_years,
        investment_goal=row.investment_goal,
        risk_score=row.risk_score,
        risk_profile_id=row.risk_profile_id,
        risk_profile_name=risk_profile_name,
        updated_at=row.updated_at,
    )
