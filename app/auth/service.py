from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest
from app.core.security import create_access_token, verify_password
from app.users.models import User


class AuthenticationError(Exception):
    pass


def authenticate_user(
    db: Session,
    credentials: LoginRequest,
) -> User:
    user = db.scalar(
        select(User).where(User.email == credentials.email)
    )

    if user is None:
        raise AuthenticationError("Invalid email or password")

    if not user.is_active:
        raise AuthenticationError("User account is inactive")

    if not verify_password(credentials.password, user.password_hash):
        raise AuthenticationError("Invalid email or password")

    user.last_login_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)

    return user


def login(
    db: Session,
    credentials: LoginRequest,
) -> str:
    user = authenticate_user(db, credentials)

    return create_access_token(str(user.id))