import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.roles.models import Role
from app.users.models import User
from app.users.repository import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_users_by_role,
)
from app.users.schemas import (
    MasterAdminCreate,
    MasterAdminUpdate,
)


class UserServiceError(Exception):
    pass


def get_master_admin_role(db: Session) -> Role:
    role = db.scalar(
        select(Role).where(
            Role.name == "MASTER ADMIN",
            Role.is_active.is_(True),
        )
    )

    if role is None:
        raise UserServiceError(
            "MASTER ADMIN role does not exist"
        )

    return role


def create_master_admin(
    db: Session,
    data: MasterAdminCreate,
) -> User:

    existing_user = get_user_by_email(
        db,
        data.email,
    )

    if existing_user is not None:
        raise UserServiceError(
            "A user with this email already exists"
        )

    if data.mobile:
        existing_mobile = db.scalar(
            select(User).where(
                User.mobile == data.mobile
            )
        )

        if existing_mobile is not None:
            raise UserServiceError(
                "A user with this mobile number already exists"
            )

    role = get_master_admin_role(db)

    user = User(
        id=uuid.uuid4(),
        role_id=role.id,
        email=data.email,
        mobile=data.mobile,
        password_hash=hash_password(data.password),
        is_active=True,
    )

    create_user(db, user)

    db.commit()
    db.refresh(user)

    return user


def list_master_admins(
    db: Session,
) -> list[User]:

    role = get_master_admin_role(db)

    return get_users_by_role(
        db,
        role.id,
    )


def update_master_admin(
    db: Session,
    user_id: uuid.UUID,
    data: MasterAdminUpdate,
) -> User:

    user = get_user_by_id(
        db,
        user_id,
    )

    if user is None:
        raise UserServiceError(
            "Master Admin not found"
        )

    role = get_master_admin_role(db)

    if user.role_id != role.id:
        raise UserServiceError(
            "User is not a Master Admin"
        )

    if data.mobile is not None:
        existing_mobile = db.scalar(
            select(User).where(
                User.mobile == data.mobile,
                User.id != user_id,
            )
        )

        if existing_mobile is not None:
            raise UserServiceError(
                "A user with this mobile number already exists"
            )

        user.mobile = data.mobile

    if data.is_active is not None:
        user.is_active = data.is_active

    db.commit()
    db.refresh(user)

    return user