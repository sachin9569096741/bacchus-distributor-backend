import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session, joinedload, selectinload
from app.audit.service import AuditService
from app.core.security import hash_password
from app.distributors.models import Distributor
from app.distributors.repository import (
    get_area,
    get_distributor_area_ids,
    get_distributor_by_code,
    get_distributor_by_id,
    get_distributor_by_user_id,
    get_distributor_zone_ids,
    get_distributors,
    get_state,
    get_user_by_email,
    get_user_by_mobile,
    get_zone,
    replace_distributor_areas,
    replace_distributor_zones,
)
from app.distributors.schemas import (
    DistributorCreate,
    DistributorUpdate,
)
from app.geography.models import Area, Zone
from app.roles.models import Role
from app.users.models import User


class DistributorServiceError(Exception):
    pass


# ============================================================
# ROLE
# ============================================================

def get_distributor_role(db: Session) -> Role:
    role = db.scalar(
        select(Role).where(
            Role.name == "DISTRIBUTOR",
            Role.is_active.is_(True),
        )
    )

    if role is None:
        raise DistributorServiceError(
            "DISTRIBUTOR role does not exist"
        )

    return role


# ============================================================
# TERRITORY VALIDATION
# ============================================================

def validate_distributor_territory(
    db: Session,
    state_id: uuid.UUID,
    zone_ids: list[uuid.UUID],
    area_ids: list[uuid.UUID],
) -> None:

    # --------------------------------------------------------
    # State
    # --------------------------------------------------------

    state = get_state(
        db,
        state_id,
    )

    if state is None:
        raise DistributorServiceError(
            "Invalid or inactive state"
        )

    if not zone_ids:
        raise DistributorServiceError(
            "At least one zone must be assigned"
        )

    if not area_ids:
        raise DistributorServiceError(
            "At least one area must be assigned"
        )

    # --------------------------------------------------------
    # Validate zones
    # --------------------------------------------------------

    for zone_id in zone_ids:

        zone = get_zone(
            db,
            zone_id,
        )

        if zone is None:
            raise DistributorServiceError(
                f"Invalid or inactive zone: {zone_id}"
            )

        if zone.state_id != state_id:
            raise DistributorServiceError(
                "Every selected zone must belong to the selected state"
            )

    # --------------------------------------------------------
    # Validate areas
    # --------------------------------------------------------

    selected_zone_ids = set(zone_ids)

    for area_id in area_ids:

        area = get_area(
            db,
            area_id,
        )

        if area is None:
            raise DistributorServiceError(
                f"Invalid or inactive area: {area_id}"
            )

        if area.state_id != state_id:
            raise DistributorServiceError(
                "Every selected area must belong to the selected state"
            )

        if area.zone_id not in selected_zone_ids:
            raise DistributorServiceError(
                "Every selected area must belong to one of the selected zones"
            )


# ============================================================
# DISTRIBUTOR CODE GENERATION
# ============================================================

def generate_distributor_code(
    db: Session,
    state_id: uuid.UUID,
    zone_ids: list[uuid.UUID],
    area_ids: list[uuid.UUID],
) -> str:

    state = get_state(
        db,
        state_id,
    )

    zone = get_zone(
        db,
        zone_ids[0],
    )

    area = get_area(
        db,
        area_ids[0],
    )

    if not state or not zone or not area:
        raise DistributorServiceError(
            "Unable to generate distributor code"
        )

    prefix = (
        f"BAC-{state.code}-"
        f"{zone.code}-"
        f"{area.code}"
    )

    for _ in range(10):

        code = (
            f"{prefix}-"
            f"D{uuid.uuid4().hex[:8].upper()}"
        )

        if get_distributor_by_code(
            db,
            code,
        ) is None:
            return code

    raise DistributorServiceError(
        "Unable to generate unique distributor code"
    )


# ============================================================
# CREATE DISTRIBUTOR
# ============================================================

def create_distributor(
    db: Session,
    data: DistributorCreate,
) -> Distributor:

    # --------------------------------------------------------
    # Check email
    # --------------------------------------------------------

    existing_user = get_user_by_email(
        db,
        data.email,
    )

    if existing_user is not None:
        raise DistributorServiceError(
            "A user with this email already exists"
        )

    # --------------------------------------------------------
    # Check mobile
    # --------------------------------------------------------

    existing_mobile = get_user_by_mobile(
        db,
        data.mobile,
    )

    if existing_mobile is not None:
        raise DistributorServiceError(
            "A user with this mobile number already exists"
        )

    # --------------------------------------------------------
    # Normalize territory
    # --------------------------------------------------------

    zone_ids = list(
        dict.fromkeys(data.zone_ids)
    )

    area_ids = list(
        dict.fromkeys(data.area_ids)
    )

    # --------------------------------------------------------
    # Validate territory
    # --------------------------------------------------------

    validate_distributor_territory(
        db,
        data.state_id,
        zone_ids,
        area_ids,
    )

    # --------------------------------------------------------
    # Get role
    # --------------------------------------------------------

    role = get_distributor_role(db)

    # --------------------------------------------------------
    # Generate code
    # --------------------------------------------------------

    distributor_code = generate_distributor_code(
        db,
        data.state_id,
        zone_ids,
        area_ids,
    )

    # --------------------------------------------------------
    # Create user
    # --------------------------------------------------------

    user = User(
        id=uuid.uuid4(),
        role_id=role.id,
        email=data.email,
        mobile=data.mobile,
        password_hash=hash_password(data.password),
        is_active=True,
    )

    # --------------------------------------------------------
    # Legacy compatibility values
    #
    # First selected zone/area remain in old columns.
    # New authorization uses mapping tables.
    # --------------------------------------------------------

    distributor = Distributor(
        id=uuid.uuid4(),
        distributor_code=distributor_code,
        business_name=data.business_name,
        owner_name=data.owner_name,
        mobile=data.mobile,
        email=data.email,
        address=data.address,
        state_id=data.state_id,
        zone_id=zone_ids[0],
        area_id=area_ids[0],
        gst_number=data.gst_number,
        license_number=data.license_number,
        credit_limit=data.credit_limit,
        user_id=user.id,
        is_active=True,
    )

    db.add(user)
    db.add(distributor)

    db.flush()

    # --------------------------------------------------------
    # Territory mappings
    # --------------------------------------------------------

    replace_distributor_zones(
        db,
        distributor.id,
        zone_ids,
    )

    replace_distributor_areas(
        db,
        distributor.id,
        area_ids,
    )

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    AuditService.log(
        db,
        actor_id=None,
        action="DISTRIBUTOR_CREATED",
        entity="distributor",
        entity_id=distributor.id,
        new_value={
            "distributor_code": distributor.distributor_code,
            "business_name": distributor.business_name,
            "owner_name": distributor.owner_name,
            "mobile": distributor.mobile,
            "email": distributor.email,
            "state_id": str(distributor.state_id),
            "zone_ids": [
                str(zone_id)
                for zone_id in zone_ids
            ],
            "area_ids": [
                str(area_id)
                for area_id in area_ids
            ],
            "gst_number": distributor.gst_number,
            "license_number": distributor.license_number,
            "credit_limit": str(
                distributor.credit_limit
            )
            if distributor.credit_limit is not None
            else None,
            "is_active": distributor.is_active,
        },
    )

    try:
        db.commit()
        db.refresh(distributor)

    except Exception:
        db.rollback()
        raise

    return distributor


# ============================================================
# LIST DISTRIBUTORS
# ============================================================

def list_distributors(
    db: Session,
) -> list[Distributor]:

    return get_distributors(db)


# ============================================================
# GET DISTRIBUTOR
# ============================================================

def get_distributor(
    db: Session,
    distributor_id: uuid.UUID,
) -> Distributor:

    distributor = get_distributor_by_id(
        db,
        distributor_id,
    )

    if distributor is None:
        raise DistributorServiceError(
            "Distributor not found"
        )

    return distributor


# ============================================================
# GET CURRENT DISTRIBUTOR
# ============================================================

def get_current_distributor(
    db: Session,
    user_id: uuid.UUID,
) -> Distributor:

    distributor = db.scalar(
        select(Distributor)
        .options(
            joinedload(Distributor.state),
            selectinload(Distributor.territory_zones)
                .joinedload("zone"),
            selectinload(Distributor.territory_areas)
                .joinedload("area"),
        )
        .where(
            Distributor.user_id == user_id
        )
    )

    if distributor is None:
        raise DistributorServiceError(
            "Distributor profile not found"
        )

    return distributor


# ============================================================
# UPDATE DISTRIBUTOR
# ============================================================

def update_distributor(
    db: Session,
    distributor_id: uuid.UUID,
    data: DistributorUpdate,
) -> Distributor:

    distributor = get_distributor_by_id(
        db,
        distributor_id,
    )

    if distributor is None:
        raise DistributorServiceError(
            "Distributor not found"
        )

    update_data = data.model_dump(
        exclude_unset=True,
    )

    # --------------------------------------------------------
    # Prevent clearing mandatory user fields
    # --------------------------------------------------------

    if (
        "email" in update_data
        and update_data["email"] is None
    ):
        raise DistributorServiceError(
            "Distributor email cannot be cleared"
        )

    if (
        "mobile" in update_data
        and update_data["mobile"] is None
    ):
        raise DistributorServiceError(
            "Distributor mobile cannot be cleared"
        )

    # --------------------------------------------------------
    # Resolve final state
    # --------------------------------------------------------

    state_id = update_data.get(
        "state_id",
        distributor.state_id,
    )

    # --------------------------------------------------------
    # Resolve current mappings
    # --------------------------------------------------------

    current_zone_ids = get_distributor_zone_ids(
        db,
        distributor.id,
    )

    current_area_ids = get_distributor_area_ids(
        db,
        distributor.id,
    )

    # Fallback for any old distributor that has not been
    # mapped for some reason.
    if not current_zone_ids and distributor.zone_id:
        current_zone_ids = [
            distributor.zone_id
        ]

    if not current_area_ids and distributor.area_id:
        current_area_ids = [
            distributor.area_id
        ]

    # --------------------------------------------------------
    # Resolve new territory
    # --------------------------------------------------------

    zone_ids = update_data.pop(
        "zone_ids",
        None,
    )

    area_ids = update_data.pop(
        "area_ids",
        None,
    )

    legacy_zone_id = update_data.pop(
        "zone_id",
        None,
    )

    legacy_area_id = update_data.pop(
        "area_id",
        None,
    )

    if zone_ids is None:
        if legacy_zone_id is not None:
            zone_ids = [legacy_zone_id]
        else:
            zone_ids = current_zone_ids

    if area_ids is None:
        if legacy_area_id is not None:
            area_ids = [legacy_area_id]
        else:
            area_ids = current_area_ids

    zone_ids = list(
        dict.fromkeys(zone_ids)
    )

    area_ids = list(
        dict.fromkeys(area_ids)
    )

    # --------------------------------------------------------
    # If state changes, the complete territory is validated
    # against the new state.
    # --------------------------------------------------------

    validate_distributor_territory(
        db,
        state_id,
        zone_ids,
        area_ids,
    )

    # --------------------------------------------------------
    # Check email uniqueness
    # --------------------------------------------------------

    if "email" in update_data:

        new_email = update_data["email"]

        existing_user = get_user_by_email(
            db,
            new_email,
        )

        if (
            existing_user is not None
            and existing_user.id != distributor.user_id
        ):
            raise DistributorServiceError(
                "A user with this email already exists"
            )

    # --------------------------------------------------------
    # Check mobile uniqueness
    # --------------------------------------------------------

    if "mobile" in update_data:

        new_mobile = update_data["mobile"]

        existing_user = get_user_by_mobile(
            db,
            new_mobile,
        )

        if (
            existing_user is not None
            and existing_user.id != distributor.user_id
        ):
            raise DistributorServiceError(
                "A user with this mobile number already exists"
            )

    # --------------------------------------------------------
    # Linked user
    # --------------------------------------------------------

    user = None

    if distributor.user_id:

        user = db.scalar(
            select(User).where(
                User.id == distributor.user_id
            )
        )

    # --------------------------------------------------------
    # Save old territory for audit
    # --------------------------------------------------------

    old_value = {
        "business_name": distributor.business_name,
        "owner_name": distributor.owner_name,
        "mobile": distributor.mobile,
        "email": distributor.email,
        "address": distributor.address,
        "state_id": str(distributor.state_id),
        "zone_ids": [
            str(zone_id)
            for zone_id in current_zone_ids
        ],
        "area_ids": [
            str(area_id)
            for area_id in current_area_ids
        ],
        "gst_number": distributor.gst_number,
        "license_number": distributor.license_number,
        "credit_limit": str(
            distributor.credit_limit
        )
        if distributor.credit_limit is not None
        else None,
        "is_active": distributor.is_active,
    }

    # --------------------------------------------------------
    # Update regular fields
    # --------------------------------------------------------

    for field, value in update_data.items():
        setattr(
            distributor,
            field,
            value,
        )

    # --------------------------------------------------------
    # Update state + legacy compatibility columns
    # --------------------------------------------------------

    distributor.state_id = state_id
    distributor.zone_id = zone_ids[0]
    distributor.area_id = area_ids[0]

    # --------------------------------------------------------
    # Replace territory mappings
    # --------------------------------------------------------

    replace_distributor_zones(
        db,
        distributor.id,
        zone_ids,
    )

    replace_distributor_areas(
        db,
        distributor.id,
        area_ids,
    )

    # --------------------------------------------------------
    # Synchronize linked user
    # --------------------------------------------------------

    if user:

        if "email" in update_data:
            user.email = update_data["email"]

        if "mobile" in update_data:
            user.mobile = update_data["mobile"]

        if "is_active" in update_data:
            user.is_active = update_data["is_active"]

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    AuditService.log(
        db,
        actor_id=None,
        action="DISTRIBUTOR_UPDATED",
        entity="distributor",
        entity_id=distributor.id,
        old_value=old_value,
        new_value={
            "business_name": distributor.business_name,
            "owner_name": distributor.owner_name,
            "mobile": distributor.mobile,
            "email": distributor.email,
            "address": distributor.address,
            "state_id": str(distributor.state_id),
            "zone_ids": [
                str(zone_id)
                for zone_id in zone_ids
            ],
            "area_ids": [
                str(area_id)
                for area_id in area_ids
            ],
            "gst_number": distributor.gst_number,
            "license_number": distributor.license_number,
            "credit_limit": str(
                distributor.credit_limit
            )
            if distributor.credit_limit is not None
            else None,
            "is_active": distributor.is_active,
        },
    )

    try:
        db.commit()
        db.refresh(distributor)

    except Exception:
        db.rollback()
        raise

    return distributor


# ============================================================
# UPDATE DISTRIBUTOR STATUS
# ============================================================

def update_distributor_status(
    db: Session,
    distributor_id: uuid.UUID,
    is_active: bool,
) -> Distributor:

    distributor = get_distributor_by_id(
        db,
        distributor_id,
    )

    if distributor is None:
        raise DistributorServiceError(
            "Distributor not found"
        )

    old_status = distributor.is_active

    distributor.is_active = is_active

    # --------------------------------------------------------
    # Keep login account synchronized
    # --------------------------------------------------------

    if distributor.user_id:

        user = db.scalar(
            select(User).where(
                User.id == distributor.user_id
            )
        )

        if user is not None:
            user.is_active = is_active

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    AuditService.log(
        db,
        actor_id=None,
        action="DISTRIBUTOR_STATUS_CHANGED",
        entity="distributor",
        entity_id=distributor.id,
        old_value={
            "is_active": old_status,
        },
        new_value={
            "is_active": is_active,
        },
    )

    try:
        db.commit()
        db.refresh(distributor)

    except Exception:
        db.rollback()
        raise

    return distributor