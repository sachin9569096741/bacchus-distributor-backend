from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.geography.models import Area, State, Zone


def get_state(
    db: Session,
    state_id: UUID,
) -> State | None:
    return db.scalar(
        select(State).where(State.id == state_id)
    )


def get_state_by_code(
    db: Session,
    code: str,
) -> State | None:
    return db.scalar(
        select(State).where(State.code == code)
    )


def get_states(db: Session) -> list[State]:
    return list(
        db.scalars(
            select(State).order_by(State.name)
        )
    )


def get_zone(
    db: Session,
    zone_id: UUID,
) -> Zone | None:
    return db.scalar(
        select(Zone).where(Zone.id == zone_id)
    )


def get_zone_by_state_code(
    db: Session,
    state_id: UUID,
    code: str,
) -> Zone | None:
    return db.scalar(
        select(Zone).where(
            Zone.state_id == state_id,
            Zone.code == code,
        )
    )


def get_zones(
    db: Session,
    state_id: UUID | None = None,
) -> list[Zone]:

    query = select(Zone)

    if state_id is not None:
        query = query.where(
            Zone.state_id == state_id
        )

    query = query.order_by(Zone.name)

    return list(db.scalars(query))


def get_area(
    db: Session,
    area_id: UUID,
) -> Area | None:
    return db.scalar(
        select(Area).where(Area.id == area_id)
    )


def get_area_by_zone_code(
    db: Session,
    zone_id: UUID,
    code: str,
) -> Area | None:
    return db.scalar(
        select(Area).where(
            Area.zone_id == zone_id,
            Area.code == code,
        )
    )


def get_areas(
    db: Session,
    zone_id: UUID | None = None,
) -> list[Area]:

    query = select(Area)

    if zone_id is not None:
        query = query.where(
            Area.zone_id == zone_id
        )

    query = query.order_by(Area.name)

    return list(db.scalars(query))