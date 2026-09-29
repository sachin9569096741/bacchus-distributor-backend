from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.users.models import User


def get_user_by_id(
    db: Session,
    user_id: UUID,
) -> User | None:
    return db.scalar(
        select(User).where(User.id == user_id)
    )


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    return db.scalar(
        select(User).where(User.email == email)
    )


def get_users_by_role(
    db: Session,
    role_id: UUID,
) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .where(User.role_id == role_id)
            .order_by(User.created_at.desc())
        )
    )


def create_user(
    db: Session,
    user: User,
) -> User:
    db.add(user)
    db.flush()
    return user


def delete_user(
    db: Session,
    user: User,
) -> None:
    db.delete(user)