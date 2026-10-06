from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.distributors.models import Distributor
from app.distributors.territory_models import (
    DistributorArea,
    DistributorZone,
)
from app.geography.models import Area, State, Zone
from app.users.models import User


# ============================================================
# DISTRIBUTOR
# ============================================================

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


# ============================================================
# USERS
# ============================================================

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


# ============================================================
# GEOGRAPHY
# ============================================================

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


# ============================================================
# DISTRIBUTOR TERRITORY
# ============================================================

def get_distributor_zone_mappings(
    db: Session,
    distributor_id: UUID,
) -> list[DistributorZone]:
    return list(
        db.scalars(
            select(DistributorZone)
            .where(
                DistributorZone.distributor_id
                == distributor_id
            )
            .order_by(DistributorZone.created_at)
        )
    )


def get_distributor_area_mappings(
    db: Session,
    distributor_id: UUID,
) -> list[DistributorArea]:
    return list(
        db.scalars(
            select(DistributorArea)
            .where(
                DistributorArea.distributor_id
                == distributor_id
            )
            .order_by(DistributorArea.created_at)
        )
    )


def get_distributor_zone_ids(
    db: Session,
    distributor_id: UUID,
) -> list[UUID]:
    return list(
        db.scalars(
            select(DistributorZone.zone_id)
            .where(
                DistributorZone.distributor_id
                == distributor_id
            )
            .order_by(DistributorZone.created_at)
        )
    )


def get_distributor_area_ids(
    db: Session,
    distributor_id: UUID,
) -> list[UUID]:
    return list(
        db.scalars(
            select(DistributorArea.area_id)
            .where(
                DistributorArea.distributor_id
                == distributor_id
            )
            .order_by(DistributorArea.created_at)
        )
    )


def replace_distributor_zones(
    db: Session,
    distributor_id: UUID,
    zone_ids: list[UUID],
) -> None:

    db.query(DistributorZone).filter(
        DistributorZone.distributor_id
        == distributor_id
    ).delete(
        synchronize_session=False,
    )

    for zone_id in zone_ids:
        db.add(
            DistributorZone(
                distributor_id=distributor_id,
                zone_id=zone_id,
            )
        )


def replace_distributor_areas(
    db: Session,
    distributor_id: UUID,
    area_ids: list[UUID],
) -> None:

    db.query(DistributorArea).filter(
        DistributorArea.distributor_id
        == distributor_id
    ).delete(
        synchronize_session=False,
    )

    for area_id in area_ids:
        db.add(
            DistributorArea(
                distributor_id=distributor_id,
                area_id=area_id,
            )
        )