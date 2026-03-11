"""Authentication service - JWT, password hashing, user management."""

import datetime
import logging
import secrets
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AuditLog, RefreshToken, User, UserSession

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict, expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update(
        {"exp": expire, "type": "access", "jti": secrets.token_urlsafe(16)}
    )
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: dict, expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
    to_encode.update(
        {"exp": expire, "type": "refresh", "jti": secrets.token_urlsafe(16)}
    )
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.datetime.utcnow():
        logger.warning(f"Account locked for user {email}")
        return None

    # For SSO users without password
    if not user.hashed_password:
        logger.warning(f"SSO user {email} attempting password login")
        return None

    if not verify_password(password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.datetime.utcnow() + datetime.timedelta(
                minutes=30
            )
            logger.warning(f"Account locked after 5 failed attempts: {email}")
        db.commit()
        return None

    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.datetime.utcnow()
    db.commit()

    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    email: str,
    password: Optional[str] = None,
    full_name: Optional[str] = None,
    username: Optional[str] = None,
    is_superuser: bool = False,
    sso_provider: Optional[str] = None,
    sso_user_id: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> User:
    """Create a new user."""
    hashed_password = get_password_hash(password) if password else None

    user = User(
        email=email,
        username=username or email.split("@")[0],
        hashed_password=hashed_password,
        full_name=full_name,
        is_superuser=is_superuser,
        is_verified=True if sso_provider else False,  # SSO users are auto-verified
        sso_provider=sso_provider,
        sso_user_id=sso_user_id,
        avatar_url=avatar_url,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def store_refresh_token(
    db: Session, user_id: int, token: str, expires_at: datetime.datetime
):
    """Store refresh token in database."""
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    db.commit()
    return refresh_token


def revoke_refresh_token(db: Session, token: str) -> bool:
    """Revoke a refresh token."""
    refresh_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if refresh_token:
        refresh_token.is_revoked = True
        refresh_token.revoked_at = datetime.datetime.utcnow()
        db.commit()
        return True
    return False


def is_refresh_token_valid(db: Session, token: str) -> bool:
    """Check if refresh token is valid."""
    refresh_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if not refresh_token:
        return False

    if refresh_token.is_revoked:
        return False

    if refresh_token.expires_at < datetime.datetime.utcnow():
        return False

    return True


def create_session(
    db: Session,
    user_id: int,
    session_token: str,
    expires_at: datetime.datetime,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> UserSession:
    """Create user session."""
    session = UserSession(
        user_id=user_id,
        session_token=session_token,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    return session


def get_session(db: Session, session_token: str) -> Optional[UserSession]:
    """Get user session by token."""
    return (
        db.query(UserSession).filter(UserSession.session_token == session_token).first()
    )


def cleanup_expired_sessions(db: Session):
    """Remove expired sessions."""
    db.query(UserSession).filter(
        UserSession.expires_at < datetime.datetime.utcnow()
    ).delete()
    db.commit()


def log_audit(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
):
    """Log security audit event."""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
    )
    db.add(audit_log)
    db.commit()


def ensure_default_admin(db: Session):
    """Create default admin user if not exists."""
    admin = get_user_by_email(db, settings.DEFAULT_ADMIN_EMAIL)
    if not admin:
        logger.info(f"Creating default admin user: {settings.DEFAULT_ADMIN_EMAIL}")
        create_user(
            db=db,
            email=settings.DEFAULT_ADMIN_EMAIL,
            password=settings.DEFAULT_ADMIN_PASSWORD,
            full_name="System Administrator",
            is_superuser=True,
        )
        # Mark as verified
        admin = get_user_by_email(db, settings.DEFAULT_ADMIN_EMAIL)
        if admin:
            admin.is_verified = True
            db.commit()
