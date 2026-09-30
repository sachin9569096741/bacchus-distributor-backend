from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_database
from app.permissions.models import Permission
from app.roles.models import Role
from app.users.models import User


def require_permission(permission_code: str) -> Callable:
    def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_database),
    ) -> User:

        permission_exists = db.scalar(
            select(Permission.id)
            .join(Permission.roles)
            .where(
                Permission.code == permission_code,
                Permission.is_active.is_(True),
                Permission.roles.any(
                    id=current_user.role_id,
                    is_active=True,
                ),
            )
        )

        if permission_exists is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return permission_dependency


def require_role(*role_names: str) -> Callable:
    def role_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_database),
    ) -> User:

        role_exists = db.scalar(
            select(Role.id).where(
                Role.id == current_user.role_id,
                Role.name.in_(role_names),
                Role.is_active.is_(True),
            )
        )

        if role_exists is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role privileges",
            )

        return current_user

    return role_dependency


def require_any_role(*role_names: str) -> Callable:
    """
    Backward-compatible alias for require_role().
    Allows one or multiple roles.
    """
    return require_role(*role_names)