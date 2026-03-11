"""Authentication router - login, register, SSO, user management."""

import datetime
import logging
from typing import Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from starlette.config import Config

from app.config import settings
from app.database import get_db
from app.dependencies import (
    get_client_ip,
    get_current_superuser,
    get_current_user,
    get_user_agent,
)
from app.models import User
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_session,
    create_user,
    decode_token,
    get_user_by_email,
    is_refresh_token_valid,
    log_audit,
    revoke_refresh_token,
    store_refresh_token,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 configuration
oauth_config = Config(environ={
    "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET,
    "MICROSOFT_CLIENT_ID": settings.MICROSOFT_CLIENT_ID,
    "MICROSOFT_CLIENT_SECRET": settings.MICROSOFT_CLIENT_SECRET,
})

oauth = OAuth(oauth_config)

# Register OAuth providers
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

if settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_CLIENT_SECRET:
    oauth.register(
        name="microsoft",
        server_metadata_url=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/v2.0/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


# Pydantic models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    is_verified: bool
    sso_provider: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime.datetime
    last_login_at: Optional[datetime.datetime]

    class Config:
        from_attributes = True


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    """Register a new user."""
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled",
        )
    
    # Check if user exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create user
    user = create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        username=user_data.username,
    )
    
    # Log audit
    log_audit(
        db=db,
        action="user_registered",
        user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    return user


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    """Login with email and password."""
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        log_audit(
            db=db,
            action="login_failed",
            details=f"Failed login attempt for {user_data.email}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            status="failed",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Store refresh token
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    store_refresh_token(db, user.id, refresh_token, expires_at)
    
    # Create session
    session_token = create_access_token(data={"sub": str(user.id), "type": "session"})
    session_expires = datetime.datetime.utcnow() + datetime.timedelta(
        seconds=settings.SESSION_MAX_AGE
    )
    create_session(
        db=db,
        user_id=user.id,
        session_token=session_token,
        expires_at=session_expires,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    # Set session cookie
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        max_age=settings.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    
    # Log audit
    log_audit(
        db=db,
        action="login_success",
        user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token."""
    if not is_refresh_token_valid(db, token_data.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    payload = decode_token(token_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    
    # Revoke old refresh token
    revoke_refresh_token(db, token_data.refresh_token)
    
    # Store new refresh token
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    store_refresh_token(db, int(user_id), new_refresh_token, expires_at)
    
    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout current user."""
    # Clear session cookie
    response.delete_cookie(key=settings.SESSION_COOKIE_NAME)
    
    # Log audit
    log_audit(
        db=db,
        action="logout",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user information."""
    return current_user


# Google OAuth2
@router.get("/google/login")
async def google_login(request: Request):
    """Initiate Google OAuth2 login."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google SSO is not configured",
        )
    
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Handle Google OAuth2 callback."""
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Google",
            )
        
        email = user_info.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google",
            )
        
        # Get or create user
        user = get_user_by_email(db, email)
        if not user:
            user = create_user(
                db=db,
                email=email,
                full_name=user_info.get("name"),
                sso_provider="google",
                sso_user_id=user_info.get("sub"),
                avatar_url=user_info.get("picture"),
            )
        
        # Create tokens and session (same as regular login)
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        session_token = create_access_token(data={"sub": str(user.id), "type": "session"})
        session_expires = datetime.datetime.utcnow() + datetime.timedelta(
            seconds=settings.SESSION_MAX_AGE
        )
        
        create_session(
            db=db,
            user_id=user.id,
            session_token=session_token,
            expires_at=session_expires,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
        
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_token,
            max_age=settings.SESSION_MAX_AGE,
            httponly=True,
            samesite="lax",
        )
        
        log_audit(
            db=db,
            action="login_google_sso",
            user_id=user.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
        
        # Redirect to dashboard
        return RedirectResponse(url="/")
        
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth failed: {str(e)}",
        )


# Microsoft OAuth2
@router.get("/microsoft/login")
async def microsoft_login(request: Request):
    """Initiate Microsoft OAuth2 login."""
    if not settings.MICROSOFT_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft SSO is not configured",
        )
    
    redirect_uri = settings.MICROSOFT_REDIRECT_URI
    return await oauth.microsoft.authorize_redirect(request, redirect_uri)


@router.get("/microsoft/callback")
async def microsoft_callback(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Handle Microsoft OAuth2 callback."""
    try:
        token = await oauth.microsoft.authorize_access_token(request)
        user_info = token.get("userinfo")
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Microsoft",
            )
        
        email = user_info.get("email") or user_info.get("preferred_username")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Microsoft",
            )
        
        # Get or create user
        user = get_user_by_email(db, email)
        if not user:
            user = create_user(
                db=db,
                email=email,
                full_name=user_info.get("name"),
                sso_provider="microsoft",
                sso_user_id=user_info.get("oid") or user_info.get("sub"),
            )
        
        # Create session (same as Google)
        session_token = create_access_token(data={"sub": str(user.id), "type": "session"})
        session_expires = datetime.datetime.utcnow() + datetime.timedelta(
            seconds=settings.SESSION_MAX_AGE
        )
        
        create_session(
            db=db,
            user_id=user.id,
            session_token=session_token,
            expires_at=session_expires,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
        
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_token,
            max_age=settings.SESSION_MAX_AGE,
            httponly=True,
            samesite="lax",
        )
        
        log_audit(
            db=db,
            action="login_microsoft_sso",
            user_id=user.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
        
        return RedirectResponse(url="/")
        
    except Exception as e:
        logger.error(f"Microsoft OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Microsoft OAuth failed: {str(e)}",
        )


# User management (Admin only)
@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """List all users (admin only)."""
    users = db.query(User).all()
    return users


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """Delete a user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": f"User {user.email} deleted successfully"}
