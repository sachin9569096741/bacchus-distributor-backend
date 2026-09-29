import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.audit.service import AuditService
from app.distributors.models import Distributor
from app.distributors.repository import (
    get_area,
    get_distributor_by_code,
    get_distributor_by_id,
    get_distributors,
    get_state,
    get_user_by_email,
    get_user_by_mobile,
    get_zone,
)
from app.distributors.schemas import (
    DistributorCreate,
    DistributorUpdate,
)
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

def validate_territory(
    db: Session,
    state_id: uuid.UUID,
    zone_id: uuid.UUID,
    area_id: uuid.UUID,
) -> None:

    state = get_state(db, state_id)

    if state is None:
        raise DistributorServiceError(
            "Invalid or inactive state"
        )

    zone = get_zone(db, zone_id)

    if zone is None:
        raise DistributorServiceError(
            "Invalid or inactive zone"
        )

    if zone.state_id != state_id:
        raise DistributorServiceError(
            "Zone does not belong to the selected state"
        )

    area = get_area(db, area_id)

    if area is None:
        raise DistributorServiceError(
            "Invalid or inactive area"
        )

    if area.zone_id != zone_id:
        raise DistributorServiceError(
            "Area does not belong to the selected zone"
        )

    if area.state_id != state_id:
        raise DistributorServiceError(
            "Area does not belong to the selected state"
        )


# ============================================================
# DISTRIBUTOR CODE GENERATION
# ============================================================

def generate_distributor_code(
    db: Session,
    state_id: uuid.UUID,
    zone_id: uuid.UUID,
    area_id: uuid.UUID,
) -> str:

    state = get_state(db, state_id)
    zone = get_zone(db, zone_id)
    area = get_area(db, area_id)

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

        if get_distributor_by_code(db, code) is None:
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
    # Validate geography
    # --------------------------------------------------------

    validate_territory(
        db,
        data.state_id,
        data.zone_id,
        data.area_id,
    )

    # --------------------------------------------------------
    # Get distributor role
    # --------------------------------------------------------

    role = get_distributor_role(db)

    # --------------------------------------------------------
    # Generate business code
    # --------------------------------------------------------

    distributor_code = generate_distributor_code(
        db,
        data.state_id,
        data.zone_id,
        data.area_id,
    )

    # --------------------------------------------------------
    # Create login user
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
    # Create distributor
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
        zone_id=data.zone_id,
        area_id=data.area_id,
        gst_number=data.gst_number,
        license_number=data.license_number,
        credit_limit=data.credit_limit,
        user_id=user.id,
        is_active=True,
    )

    db.add(user)
    db.add(distributor)

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
            "zone_id": str(distributor.zone_id),
            "area_id": str(distributor.area_id),
            "gst_number": distributor.gst_number,
            "license_number": distributor.license_number,
            "credit_limit": str(distributor.credit_limit),
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

    old_value = {
        field: getattr(distributor, field)
        for field in update_data
    }

    # --------------------------------------------------------
    # Prevent clearing mandatory user fields
    # --------------------------------------------------------

    if "email" in update_data and update_data["email"] is None:
        raise DistributorServiceError(
            "Distributor email cannot be cleared"
        )

    if "mobile" in update_data and update_data["mobile"] is None:
        raise DistributorServiceError(
            "Distributor mobile cannot be cleared"
        )

    # --------------------------------------------------------
    # Resolve final territory
    # --------------------------------------------------------

    state_id = update_data.get(
        "state_id",
        distributor.state_id,
    )

    zone_id = update_data.get(
        "zone_id",
        distributor.zone_id,
    )

    area_id = update_data.get(
        "area_id",
        distributor.area_id,
    )

    # --------------------------------------------------------
    # Validate territory
    # --------------------------------------------------------

    validate_territory(
        db,
        state_id,
        zone_id,
        area_id,
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
    # Get linked user
    # --------------------------------------------------------

    user = None

    if distributor.user_id:

        user = db.scalar(
            select(User).where(
                User.id == distributor.user_id
            )
        )

    # --------------------------------------------------------
    # Update distributor
    # --------------------------------------------------------

    for field, value in update_data.items():
        setattr(
            distributor,
            field,
            value,
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
    # Audit + Commit
    # --------------------------------------------------------

    AuditService.log(
        db,
        actor_id=None,
        action="DISTRIBUTOR_UPDATED",
        entity="distributor",
        entity_id=distributor.id,
        old_value={
            key: str(value) if isinstance(value, uuid.UUID) else value
            for key, value in old_value.items()
        },
        new_value={
            key: str(getattr(distributor, key))
            if isinstance(getattr(distributor, key), uuid.UUID)
            else getattr(distributor, key)
            for key in update_data
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

    # --------------------------------------------------------
    # Update distributor status
    # --------------------------------------------------------

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
    # Audit + Commit
    # --------------------------------------------------------

    AuditService.log(
        db,
        actor_id=None,
        action="DISTRIBUTOR_STATUS_CHANGED",
        entity="distributor",
        entity_id=distributor.id,
        old_value={"is_active": old_status},
        new_value={"is_active": is_active},
    )

    try:
        db.commit()
        db.refresh(distributor)

    except Exception:
        db.rollback()
        raise

    return distributor