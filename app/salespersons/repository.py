from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.distributors.models import Distributor
from app.geography.models import Area, State, Zone
from app.salespersons.models import Salesperson
from app.users.models import User


# ============================================================
# SALESPERSON
# ============================================================

def get_salesperson_by_id(
    db: Session,
    salesperson_id: UUID,
) -> Salesperson | None:
    return db.scalar(
        select(Salesperson).where(
            Salesperson.id == salesperson_id
        )
    )


def get_salesperson_by_code(
    db: Session,
    salesperson_code: str,
) -> Salesperson | None:
    return db.scalar(
        select(Salesperson).where(
            Salesperson.salesperson_code == salesperson_code
        )
    )


def get_salesperson_by_employee_code(
    db: Session,
    employee_code: str,
) -> Salesperson | None:
    return db.scalar(
        select(Salesperson).where(
            Salesperson.employee_code == employee_code
        )
    )


def get_salesperson_by_user_id(
    db: Session,
    user_id: UUID,
) -> Salesperson | None:
    return db.scalar(
        select(Salesperson).where(
            Salesperson.user_id == user_id
        )
    )


def get_salesperson_by_mobile(
    db: Session,
    mobile: str,
) -> Salesperson | None:
    return db.scalar(
        select(Salesperson).where(
            Salesperson.mobile == mobile
        )
    )


def get_salesperson_by_email(
    db: Session,
    email: str,
) -> Salesperson | None:
    return db.scalar(
        select(Salesperson).where(
            Salesperson.email == email
        )
    )


def get_salespersons(
    db: Session,
) -> list[Salesperson]:
    return list(
        db.scalars(
            select(Salesperson).order_by(
                Salesperson.created_at.desc()
            )
        ).all()
    )


def get_salespersons_by_distributor(
    db: Session,
    distributor_id: UUID,
) -> list[Salesperson]:
    return list(
        db.scalars(
            select(Salesperson)
            .where(
                Salesperson.distributor_id == distributor_id
            )
            .order_by(
                Salesperson.created_at.desc()
            )
        ).all()
    )


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
# USER
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