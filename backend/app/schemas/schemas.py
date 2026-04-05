from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


# ── Auth Schemas ────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name:     str       = Field(..., min_length=2, max_length=100)
    email:    EmailStr
    password: str       = Field(..., min_length=6)


class UserLogin(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      int
    name:         str
    email:        str


class UserOut(BaseModel):
    user_id:    int
    name:       str
    email:      str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Profile Schemas ─────────────────────────────────────────────────────────

class ProfileCreate(BaseModel):
    monthly_income:           float = Field(..., gt=0)
    monthly_expenses:         float = Field(..., gt=0)
    investment_amount:        float = Field(..., gt=0)
    investment_horizon_years: int   = Field(..., ge=1, le=40)
    investment_goal:          str   = Field(..., min_length=2, max_length=100)

    @field_validator("monthly_expenses")
    @classmethod
    def expenses_less_than_income(cls, v, info):
        if "monthly_income" in info.data and v >= info.data["monthly_income"]:
            raise ValueError("Monthly expenses must be less than monthly income")
        return v


class ProfileUpdate(ProfileCreate):
    pass


class ProfileOut(BaseModel):
    profile_id:               int
    user_id:                  int
    monthly_income:           float
    monthly_expenses:         float
    investment_amount:        float
    investment_horizon_years: int
    investment_goal:          str
    risk_score:               Optional[int]
    risk_profile_id:          Optional[int]
    risk_profile_name:        Optional[str] = None
    updated_at:               datetime

    class Config:
        from_attributes = True


# ── Questionnaire Schemas ───────────────────────────────────────────────────

class QuestionnaireAnswer(BaseModel):
    question_id: int = Field(..., ge=1, le=7)
    answer:      int = Field(..., ge=1, le=4)   # 1=lowest, 4=highest risk


class QuestionnaireSubmit(BaseModel):
    answers: list[QuestionnaireAnswer] = Field(..., min_length=7, max_length=7)


class QuestionnaireResult(BaseModel):
    risk_score:      int
    risk_profile_id: int
    profile_name:    str
    description:     str


# ── Portfolio Schemas ───────────────────────────────────────────────────────

class PortfolioPositionOut(BaseModel):
    position_id:           int
    instrument_id:         int
    instrument_name:       str
    ticker:                Optional[str]
    instrument_type:       Optional[str]
    fund_house:            Optional[str]
    asset_class:           str
    allocation_percentage: float
    allocated_amount:      float

    class Config:
        from_attributes = True


class PortfolioOut(BaseModel):
    portfolio_id:     int
    user_id:          int
    model_name:       str
    risk_profile:     str
    total_investment: float
    is_active:        bool
    version:          int
    generated_at:     datetime
    positions:        list[PortfolioPositionOut]

    class Config:
        from_attributes = True


class AssetClassSummaryOut(BaseModel):
    asset_class:           str
    total_allocation_pct:  float
    total_allocated_amount: float


class ExpectedReturnsOut(BaseModel):
    weighted_return_1y: float
    weighted_return_3y: float
    weighted_return_5y: float


class PortfolioCompareOut(BaseModel):
    current_portfolio:    list[AssetClassSummaryOut]
    compared_model_name:  str
    compared_allocations: list[dict]


# ── Reference Data Schemas ──────────────────────────────────────────────────

class InstrumentOut(BaseModel):
    instrument_id:   int
    name:            str
    ticker:          Optional[str]
    asset_class:     str
    instrument_type: Optional[str]
    fund_house:      Optional[str]
    return_1y:       Optional[float] = None
    return_3y:       Optional[float] = None
    return_5y:       Optional[float] = None

    class Config:
        from_attributes = True


class RiskProfileOut(BaseModel):
    risk_profile_id: int
    profile_name:    str
    min_score:       int
    max_score:       int
    description:     Optional[str]

    class Config:
        from_attributes = True


class PortfolioModelOut(BaseModel):
    model_id:        int
    model_name:      str
    risk_profile_id: int
    risk_profile:    str
    description:     Optional[str]

    class Config:
        from_attributes = True
