import uuid

from sqlalchemy.orm import Session

from app.geography.models import Area, State, Zone
from app.geography.repository import (
    get_area,
    get_area_by_zone_code,
    get_areas,
    get_state,
    get_state_by_code,
    get_states,
    get_zone,
    get_zone_by_state_code,
    get_zones,
)
from app.geography.schemas import (
    AreaCreate,
    AreaUpdate,
    StateCreate,
    StateUpdate,
    ZoneCreate,
    ZoneUpdate,
)


class GeographyServiceError(Exception):
    pass


# -------------------------
# STATE
# -------------------------

def create_state(
    db: Session,
    data: StateCreate,
) -> State:

    if get_state_by_code(db, data.code) is not None:
        raise GeographyServiceError(
            "State code already exists"
        )

    state = State(
        id=uuid.uuid4(),
        name=data.name,
        code=data.code,
        is_active=True,
    )

    db.add(state)
    db.commit()
    db.refresh(state)

    return state


def list_states(
    db: Session,
) -> list[State]:

    return get_states(db)


def update_state(
    db: Session,
    state_id: uuid.UUID,
    data: StateUpdate,
) -> State:

    state = get_state(db, state_id)

    if state is None:
        raise GeographyServiceError(
            "State not found"
        )

    values = data.model_dump(exclude_unset=True)

    if "code" in values:
        existing = get_state_by_code(
            db,
            values["code"],
        )

        if (
            existing is not None
            and existing.id != state_id
        ):
            raise GeographyServiceError(
                "State code already exists"
            )

    for field, value in values.items():
        setattr(state, field, value)

    db.commit()
    db.refresh(state)

    return state


# -------------------------
# ZONE
# -------------------------

def create_zone(
    db: Session,
    data: ZoneCreate,
) -> Zone:

    state = get_state(
        db,
        data.state_id,
    )

    if state is None:
        raise GeographyServiceError(
            "State not found"
        )

    if not state.is_active:
        raise GeographyServiceError(
            "State is inactive"
        )

    if get_zone_by_state_code(
        db,
        data.state_id,
        data.code,
    ) is not None:
        raise GeographyServiceError(
            "Zone code already exists in this state"
        )

    zone = Zone(
        id=uuid.uuid4(),
        state_id=data.state_id,
        name=data.name,
        code=data.code,
        is_active=True,
    )

    db.add(zone)
    db.commit()
    db.refresh(zone)

    return zone


def list_zones(
    db: Session,
    state_id: uuid.UUID | None = None,
) -> list[Zone]:

    return get_zones(db, state_id)


def update_zone(
    db: Session,
    zone_id: uuid.UUID,
    data: ZoneUpdate,
) -> Zone:

    zone = get_zone(db, zone_id)

    if zone is None:
        raise GeographyServiceError(
            "Zone not found"
        )

    values = data.model_dump(exclude_unset=True)

    if "code" in values:
        existing = get_zone_by_state_code(
            db,
            zone.state_id,
            values["code"],
        )

        if (
            existing is not None
            and existing.id != zone_id
        ):
            raise GeographyServiceError(
                "Zone code already exists in this state"
            )

    for field, value in values.items():
        setattr(zone, field, value)

    db.commit()
    db.refresh(zone)

    return zone


# -------------------------
# AREA
# -------------------------

def create_area(
    db: Session,
    data: AreaCreate,
) -> Area:

    state = get_state(
        db,
        data.state_id,
    )

    if state is None:
        raise GeographyServiceError(
            "State not found"
        )

    if not state.is_active:
        raise GeographyServiceError(
            "State is inactive"
        )

    zone = get_zone(
        db,
        data.zone_id,
    )

    if zone is None:
        raise GeographyServiceError(
            "Zone not found"
        )

    if not zone.is_active:
        raise GeographyServiceError(
            "Zone is inactive"
        )

    if zone.state_id != data.state_id:
        raise GeographyServiceError(
            "Zone does not belong to the selected state"
        )

    if get_area_by_zone_code(
        db,
        data.zone_id,
        data.code,
    ) is not None:
        raise GeographyServiceError(
            "Area code already exists in this zone"
        )

    area = Area(
        id=uuid.uuid4(),
        state_id=data.state_id,
        zone_id=data.zone_id,
        name=data.name,
        code=data.code,
        is_active=True,
    )

    db.add(area)
    db.commit()
    db.refresh(area)

    return area


def list_areas(
    db: Session,
    zone_id: uuid.UUID | None = None,
) -> list[Area]:

    return get_areas(db, zone_id)


def update_area(
    db: Session,
    area_id: uuid.UUID,
    data: AreaUpdate,
) -> Area:

    area = get_area(db, area_id)

    if area is None:
        raise GeographyServiceError(
            "Area not found"
        )

    values = data.model_dump(exclude_unset=True)

    if "code" in values:
        existing = get_area_by_zone_code(
            db,
            area.zone_id,
            values["code"],
        )

        if (
            existing is not None
            and existing.id != area_id
        ):
            raise GeographyServiceError(
                "Area code already exists in this zone"
            )

    for field, value in values.items():
        setattr(area, field, value)

    db.commit()
    db.refresh(area)

    return area