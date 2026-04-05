from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    get_current_user_from_refresh,
)
from app.schemas.schemas import UserCreate, UserLogin, TokenResponse
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()
COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, response: Response, db: AsyncSession = Depends(get_db)):
    # Check email uniqueness
    existing = await db.execute(
        text("SELECT user_id FROM users WHERE email = :email"),
        {"email": payload.email},
    )
    if existing.fetchone():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Insert user
    result = await db.execute(
        text("""
            INSERT INTO users (name, email, password_hash)
            VALUES (:name, :email, :password_hash)
            RETURNING user_id, name, email
        """),
        {
            "name":          payload.name,
            "email":         payload.email,
            "password_hash": hash_password(payload.password),
        },
    )
    await db.commit()
    user = result.fetchone()

    access_token  = create_access_token({"sub": str(user.user_id)})
    refresh_token = create_refresh_token({"sub": str(user.user_id)})
    _set_refresh_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token,
        user_id=user.user_id,
        name=user.name,
        email=user.email,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT user_id, name, email, password_hash FROM users WHERE email = :email"),
        {"email": payload.email},
    )
    user = result.fetchone()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token  = create_access_token({"sub": str(user.user_id)})
    refresh_token = create_refresh_token({"sub": str(user.user_id)})
    _set_refresh_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token,
        user_id=user.user_id,
        name=user.name,
        email=user.email,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_from_refresh),
):
    user_id = int(payload["sub"])
    result = await db.execute(
        text("SELECT user_id, name, email FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    )
    user = result.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token  = create_access_token({"sub": str(user.user_id)})
    refresh_token = create_refresh_token({"sub": str(user.user_id)})
    _set_refresh_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token,
        user_id=user.user_id,
        name=user.name,
        email=user.email,
    )


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


def _set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        max_age=COOKIE_MAX_AGE,
        samesite="lax",
        secure=False,   # Set True in production with HTTPS
    )
