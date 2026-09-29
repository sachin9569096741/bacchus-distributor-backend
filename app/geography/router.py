from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_database
from app.geography.schemas import (
    AreaCreate,
    AreaResponse,
    AreaUpdate,
    StateCreate,
    StateResponse,
    StateUpdate,
    ZoneCreate,
    ZoneResponse,
    ZoneUpdate,
)
from app.geography.service import (
    GeographyServiceError,
    create_area,
    create_state,
    create_zone,
    list_areas,
    list_states,
    list_zones,
    update_area,
    update_state,
    update_zone,
)
from app.permissions.dependencies import require_role
from app.users.models import User


router = APIRouter(
    prefix="/geography",
    tags=["Geography"],
)


# =========================
# STATES
# =========================

@router.post(
    "/states",
    response_model=StateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_state_endpoint(
    data: StateCreate,
    db: Session = Depends(get_database),
    _: User = Depends(
        require_role("MASTER ADMIN")
    ),
):
    try:
        return create_state(db, data)
    except GeographyServiceError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/states",
    response_model=list[StateResponse],
)
def list_states_endpoint(
    db: Session = Depends(get_database),
    _: User = Depends(
        require_role("MASTER ADMIN")
    ),
):
    return list_states(db)


@router.patch(
    "/states/{state_id}",
    response_model=StateResponse,
)
def update_state_endpoint(
    state_id: UUID,
    data: StateUpdate,
    db: Session = Depends(get_database),
    _: User = Depends(
        require_role("MASTER ADMIN")
    ),
):
    try:
        return update_state(
            db,
            state_id,
            data,
        )
    except GeographyServiceError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================
# ZONES
# =========================

@router.post(
    "/zones",
    response_model=ZoneResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_zone_endpoint(
    data: ZoneCreate,
    db: Session = Depends(get_database),
    _: User = Depends(
        require_role("MASTER ADMIN")
    ),
):
    try:
        return create_zone(db, data)
    except GeographyServiceError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/zones",
    response_model=list[ZoneResponse],
)
def list_zones_endpoint(
    state_id: UUID | None = None,
    db: Session = Depends(get_database),
    _: User = Depends(
        require_role("MASTER ADMIN")
    ),
):
    return list_zones(db, state_id)


@router.patch(
    "/zones/{zone_id}",
    response_model=ZoneResponse,
)
def update_zone_endpoint(
    zone_id: UUID,
    data: ZoneUpdate,
    db: Session = Depends(get_database),
    _: User = Depends(
        require_role("MASTER ADMIN")
    ),
):
    try:
        return update_zone(
            db,
            zone_id,
            data,
        )
    except GeographyServiceError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================
# AREAS
# =========================

@router.post(
    "/areas",
    response_model=AreaResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_area_endpoint(
    data: AreaCreate,
    db: Session = Depends(get_database),
    _: User = Depends(
        require_role("MASTER ADMIN")
    ),
):
    try:
        return create_area(db, data)
    except GeographyServiceError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/areas",
    response_model=list[AreaResponse],
)
def list_areas_endpoint(
    zone_id: UUID | None = None,
    db: Session = Depends(get_database),
    _: User = Depends(
        require_role("MASTER ADMIN")
    ),
):
    return list_areas(db, zone_id)


@router.patch(
    "/areas/{area_id}",
    response_model=AreaResponse,
)
def update_area_endpoint(
    area_id: UUID,
    data: AreaUpdate,
    db: Session = Depends(get_database),
    _: User = Depends(
        require_role("MASTER ADMIN")
    ),
):
    try:
        return update_area(
            db,
            area_id,
            data,
        )
    except GeographyServiceError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )