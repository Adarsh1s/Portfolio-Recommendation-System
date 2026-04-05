from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.schemas import QuestionnaireSubmit, QuestionnaireResult
from app.services.risk_engine import calculate_risk_score, QUESTIONNAIRE_DEFINITIONS

router = APIRouter(prefix="/questionnaire", tags=["Questionnaire"])


@router.get("/questions")
async def get_questions():
    """Return all 7 MCQ questions with their options."""
    return {"questions": QUESTIONNAIRE_DEFINITIONS}


@router.post("/submit", response_model=QuestionnaireResult)
async def submit_questionnaire(
    payload: QuestionnaireSubmit,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Verify profile exists first
    profile_check = await db.execute(
        text("SELECT profile_id FROM user_profiles WHERE user_id = :uid"),
        {"uid": user_id},
    )
    if not profile_check.fetchone():
        raise HTTPException(
            status_code=400,
            detail="Complete your financial profile first before submitting the questionnaire.",
        )

    # Calculate risk score in Python
    risk_score = calculate_risk_score(payload.answers)

    # Call PostgreSQL stored function to get risk_profile_id
    profile_result = await db.execute(
        text("SELECT get_risk_profile_id(:score)"),
        {"score": risk_score},
    )
    risk_profile_id = profile_result.scalar()

    # Update user_profiles (triggers audit log via DB trigger)
    await db.execute(
        text("""
            UPDATE user_profiles
            SET risk_score = :score, risk_profile_id = :profile_id
            WHERE user_id = :user_id
        """),
        {"score": risk_score, "profile_id": risk_profile_id, "user_id": user_id},
    )
    await db.commit()

    # Fetch risk profile details for response
    rp_result = await db.execute(
        text("SELECT profile_name, description FROM risk_profiles WHERE risk_profile_id = :pid"),
        {"pid": risk_profile_id},
    )
    rp = rp_result.fetchone()

    return QuestionnaireResult(
        risk_score=risk_score,
        risk_profile_id=risk_profile_id,
        profile_name=rp.profile_name,
        description=rp.description,
    )
