from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.distributors.models import Distributor
from app.geography.models import Area, State, Zone
from app.salespersons.models import Salesperson
from app.sellers.models import Seller


def get_seller_by_id(
    db: Session,
    seller_id: UUID,
) -> Seller | None:
    return db.scalar(
        select(Seller).where(Seller.id == seller_id)
    )


def get_seller_by_code(
    db: Session,
    seller_code: str,
) -> Seller | None:
    return db.scalar(
        select(Seller).where(Seller.seller_code == seller_code)
    )


def get_seller_by_mobile(
    db: Session,
    mobile: str,
) -> Seller | None:
    return db.scalar(
        select(Seller).where(Seller.mobile == mobile)
    )


def get_seller_by_email(
    db: Session,
    email: str,
) -> Seller | None:
    return db.scalar(
        select(Seller).where(Seller.email == email)
    )


def get_sellers(
    db: Session,
) -> list[Seller]:
    return list(
        db.scalars(
            select(Seller).order_by(Seller.created_at.desc())
        ).all()
    )


def get_sellers_by_distributor(
    db: Session,
    distributor_id: UUID,
) -> list[Seller]:
    return list(
        db.scalars(
            select(Seller)
            .where(Seller.distributor_id == distributor_id)
            .order_by(Seller.created_at.desc())
        ).all()
    )


def get_sellers_by_salesperson(
    db: Session,
    salesperson_id: UUID,
) -> list[Seller]:
    return list(
        db.scalars(
            select(Seller)
            .where(Seller.salesperson_id == salesperson_id)
            .order_by(Seller.created_at.desc())
        ).all()
    )


def get_distributor_by_id(
    db: Session,
    distributor_id: UUID,
) -> Distributor | None:
    return db.scalar(
        select(Distributor).where(
            Distributor.id == distributor_id
        )
    )


def get_salesperson_by_id(
    db: Session,
    salesperson_id: UUID,
) -> Salesperson | None:
    return db.scalar(
        select(Salesperson).where(
            Salesperson.id == salesperson_id
        )
    )


def get_state_by_id(
    db: Session,
    state_id: UUID,
) -> State | None:
    return db.scalar(
        select(State).where(
            State.id == state_id,
            State.is_active.is_(True),
        )
    )


def get_zone_by_id(
    db: Session,
    zone_id: UUID,
) -> Zone | None:
    return db.scalar(
        select(Zone).where(
            Zone.id == zone_id,
            Zone.is_active.is_(True),
        )
    )


def get_area_by_id(
    db: Session,
    area_id: UUID,
) -> Area | None:
    return db.scalar(
        select(Area).where(
            Area.id == area_id,
            Area.is_active.is_(True),
        )
    )