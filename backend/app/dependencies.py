"""Dependency injection providers for FastAPI routes.

This module defines reusable dependencies that are injected into route
handlers via FastAPI's Depends() mechanism. Each dependency manages its
own lifecycle (e.g., database sessions are opened and closed per request).
"""

from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings, get_settings

# ─── Security Scheme ─────────────────────────────────────────────────────────
_bearer_scheme = HTTPBearer(auto_error=False)


# ─── Database Engine (lazy initialization) ───────────────────────────────────
_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine(settings: Settings):
    """Get or create the async database engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.APP_ENV == "development",
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _engine


def _get_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _session_factory
    if _session_factory is None:
        engine = _get_engine(settings)
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session per request.

    The session is automatically committed on success or rolled back
    on exception, then closed regardless of outcome.

    Usage:
        @router.get("/items")
        async def list_items(db: Annotated[AsyncSession, Depends(get_db)]):
            ...
    """
    factory = _get_session_factory(settings)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Extract and validate the current user from the JWT bearer token.

    Returns a dict containing at minimum:
        - user_id: str (UUID)
        - email: str

    Raises HTTPException 401 if the token is missing, expired, or invalid.

    Usage:
        @router.get("/profile")
        async def get_profile(user: Annotated[dict, Depends(get_current_user)]):
            ...
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user_id: str | None = payload.get("sub")
    email: str | None = payload.get("email")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"user_id": user_id, "email": email}
