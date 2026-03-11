"""FastAPI dependencies for authentication and authorization."""

from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.services.auth import decode_token, get_session, get_user_by_id

security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session_cookie: Optional[str] = Cookie(None, alias=settings.SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Get current user from JWT token or session cookie (optional)."""
    if not settings.AUTH_ENABLED:
        # If auth is disabled, return a mock admin user
        mock_user = User(
            id=1,
            email="admin@localhost",
            username="admin",
            full_name="Administrator",
            is_superuser=True,
            is_active=True,
            is_verified=True,
        )
        return mock_user

    user = None

    # Try Bearer token first
    if credentials:
        token = credentials.credentials
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            user_id = payload.get("sub")
            if user_id:
                user = get_user_by_id(db, int(user_id))

    # Try session cookie if no bearer token
    if not user and session_cookie:
        session = get_session(db, session_cookie)
        if session:
            user = get_user_by_id(db, session.user_id)

    return user


async def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Get current user (required - raises exception if not authenticated)."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return current_user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current superuser (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def get_client_ip(request: Request) -> Optional[str]:
    """Get client IP address from request."""
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    elif "x-real-ip" in request.headers:
        return request.headers["x-real-ip"]
    return request.client.host if request.client else None


def get_user_agent(request: Request) -> Optional[str]:
    """Get user agent from request."""
    return request.headers.get("user-agent")
