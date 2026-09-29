from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.distributors.models import Distributor
from app.geography.models import Area, State, Zone
from app.users.models import User


def get_distributor_by_id(
    db: Session,
    distributor_id: UUID,
) -> Distributor | None:
    return db.scalar(
        select(Distributor).where(
            Distributor.id == distributor_id
        )
    )


def get_distributor_by_code(
    db: Session,
    distributor_code: str,
) -> Distributor | None:
    return db.scalar(
        select(Distributor).where(
            Distributor.distributor_code == distributor_code
        )
    )


def get_distributors(
    db: Session,
) -> list[Distributor]:
    return list(
        db.scalars(
            select(Distributor)
            .order_by(Distributor.created_at.desc())
        )
    )

def get_distributor_by_user_id(
    db: Session,
    user_id: UUID,
) -> Distributor | None:
    return db.scalar(
        select(Distributor).where(
            Distributor.user_id == user_id
        )
    )
def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    return db.scalar(
        select(User).where(
            User.email == email
        )
    )


def get_user_by_mobile(
    db: Session,
    mobile: str,
) -> User | None:
    return db.scalar(
        select(User).where(
            User.mobile == mobile
        )
    )


def get_state(
    db: Session,
    state_id: UUID,
) -> State | None:
    return db.scalar(
        select(State).where(
            State.id == state_id,
            State.is_active.is_(True),
        )
    )


def get_zone(
    db: Session,
    zone_id: UUID,
) -> Zone | None:
    return db.scalar(
        select(Zone).where(
            Zone.id == zone_id,
            Zone.is_active.is_(True),
        )
    )


def get_area(
    db: Session,
    area_id: UUID,
) -> Area | None:
    return db.scalar(
        select(Area).where(
            Area.id == area_id,
            Area.is_active.is_(True),
        )
    )