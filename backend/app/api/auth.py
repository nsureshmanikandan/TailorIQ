"""Authentication API routes.

Provides endpoints for user registration, login, token refresh,
and password reset. Follows security best practices:
- Never reveals whether an email exists on failed login
- Validates password complexity on registration
- Returns consistent responses for password reset regardless of email existence
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.dependencies import get_db
from app.models.db import User
from app.schemas.auth import (
    LoginRequest,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    hash_password,
    validate_password_complexity,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Register a new user with email and password.

    Validates password complexity and checks for existing email.
    Returns user_id and confirmation message on success.
    """
    # Validate password complexity
    if not validate_password_complexity(body.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Password must be at least 8 characters and include "
                "uppercase, lowercase, digit, and special character."
            ),
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == body.email))
    existing_user = result.scalar_one_or_none()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create user
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.flush()

    logger.info("User registered: %s", user.id)
    return {"user_id": str(user.id), "message": "Registration successful."}


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Authenticate user with email and password.

    Returns JWT access and refresh tokens on success.
    Returns a generic error on failure to avoid revealing whether the email exists.
    """
    # Fetch user by email
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Generic error message to not reveal email existence
    invalid_credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        raise invalid_credentials_exc

    # OAuth-only users cannot login with password
    if user.password_hash is None:
        raise invalid_credentials_exc

    if not verify_password(body.password, user.password_hash):
        raise invalid_credentials_exc

    # Generate tokens
    access_token = create_access_token(str(user.id), user.email, settings)
    refresh_token = create_refresh_token(str(user.id), settings)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Refresh an access token using a valid refresh token.

    Validates the refresh token and issues a new access/refresh token pair.
    """
    token = body.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token is required.",
        )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue new tokens
    access_token = create_access_token(str(user.id), user.email, settings)
    new_refresh_token = create_refresh_token(str(user.id), settings)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/password-reset/request", response_model=dict)
async def request_password_reset(
    body: PasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Request a password reset email.

    Always returns the same response regardless of whether the email
    exists, to prevent email enumeration attacks.
    """
    # Check if user exists (for internal logging only)
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is not None:
        # In a production implementation, this would queue an email
        # with a signed reset token. For now, we log the intent.
        logger.info("Password reset requested for user: %s", user.id)

    # Always return the same response to prevent email enumeration
    return {
        "message": "If an account with that email exists, a password reset link has been sent."
    }
