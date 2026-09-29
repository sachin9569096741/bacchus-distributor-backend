import uuid
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.audit.service import AuditService
from app.distributors.models import Distributor
from app.geography.models import Area, State, Zone
from app.roles.models import Role
from app.salespersons.models import Salesperson
from app.salespersons.repository import (
    get_area,
    get_distributor_by_id,
    get_distributor_by_user_id,
    get_salesperson_by_code,
    get_salesperson_by_employee_code,
    get_salesperson_by_id,
    get_salesperson_by_mobile,
    get_salesperson_by_user_id,
    get_salespersons,
    get_salespersons_by_distributor,
    get_state,
    get_user_by_email,
    get_user_by_mobile,
    get_zone,
)
from app.salespersons.schemas import (
    SalespersonCreate,
    SalespersonUpdate,
)
from app.users.models import User


class SalespersonServiceError(Exception):
    pass


# ============================================================
# ROLE
# ============================================================

def get_salesperson_role(db: Session) -> Role:
    role = db.scalar(
        select(Role).where(
            Role.name == "SALESPERSON",
            Role.is_active.is_(True),
        )
    )

    if role is None:
        raise SalespersonServiceError(
            "SALESPERSON role does not exist"
        )

    return role


# ============================================================
# DISTRIBUTOR VALIDATION
# ============================================================

def validate_distributor(
    db: Session,
    distributor_id: UUID,
) -> Distributor:

    distributor = get_distributor_by_id(
        db,
        distributor_id,
    )

    if distributor is None:
        raise SalespersonServiceError(
            "Distributor not found"
        )

    if not distributor.is_active:
        raise SalespersonServiceError(
            "Distributor is inactive"
        )

    return distributor


# ============================================================
# DISTRIBUTOR SCOPE
# ============================================================

def validate_distributor_scope(
    db: Session,
    current_user: User,
    distributor_id: UUID,
) -> Distributor:
    """
    Ensures the authenticated user is allowed to operate
    within the requested distributor scope.

    MASTER ADMIN / SUPER ADMIN:
        Can access any distributor.

    DISTRIBUTOR:
        Can access only their own distributor.
    """

    distributor = validate_distributor(
        db,
        distributor_id,
    )

    role = current_user.role

    if role is None:
        raise SalespersonServiceError(
            "User role not found"
        )

    if role.name in {
        "SUPER ADMIN",
        "MASTER ADMIN",
    }:
        return distributor

    if role.name == "DISTRIBUTOR":

        if distributor.user_id != current_user.id:
            raise SalespersonServiceError(
                "You are not authorized to access this distributor"
            )

        return distributor

    raise SalespersonServiceError(
        "You are not authorized to access this distributor"
    )


# ============================================================
# TERRITORY VALIDATION
# ============================================================

def validate_territory(
    db: Session,
    distributor: Distributor,
    state_id: UUID,
    zone_id: UUID,
    area_id: UUID,
) -> None:

    state = get_state(
        db,
        state_id,
    )

    if state is None:
        raise SalespersonServiceError(
            "Invalid or inactive state"
        )

    zone = get_zone(
        db,
        zone_id,
    )

    if zone is None:
        raise SalespersonServiceError(
            "Invalid or inactive zone"
        )

    if zone.state_id != state_id:
        raise SalespersonServiceError(
            "Zone does not belong to the selected state"
        )

    area = get_area(
        db,
        area_id,
    )

    if area is None:
        raise SalespersonServiceError(
            "Invalid or inactive area"
        )

    if area.zone_id != zone_id:
        raise SalespersonServiceError(
            "Area does not belong to the selected zone"
        )

    if area.state_id != state_id:
        raise SalespersonServiceError(
            "Area does not belong to the selected state"
        )

    # --------------------------------------------------------
    # Salesperson must remain inside distributor territory
    # --------------------------------------------------------

    if distributor.state_id != state_id:
        raise SalespersonServiceError(
            "Salesperson state must match distributor state"
        )

    if distributor.zone_id != zone_id:
        raise SalespersonServiceError(
            "Salesperson zone must match distributor zone"
        )

    if distributor.area_id != area_id:
        raise SalespersonServiceError(
            "Salesperson area must match distributor area"
        )


# ============================================================
# SALESPERSON CODE
# ============================================================

def generate_salesperson_code(
    db: Session,
    distributor: Distributor,
) -> str:

    prefix = (
        f"{distributor.distributor_code}-SP"
    )

    for _ in range(10):

        code = (
            f"{prefix}-"
            f"{uuid.uuid4().hex[:8].upper()}"
        )

        if get_salesperson_by_code(
            db,
            code,
        ) is None:
            return code

    raise SalespersonServiceError(
        "Unable to generate unique salesperson code"
    )


# ============================================================
# CREATE SALESPERSON
# ============================================================

def create_salesperson(
    db: Session,
    data: SalespersonCreate,
    current_user: User,
) -> Salesperson:

    # --------------------------------------------------------
    # Validate distributor scope
    # --------------------------------------------------------

    distributor = validate_distributor_scope(
        db,
        current_user,
        data.distributor_id,
    )

    # --------------------------------------------------------
    # Validate territory
    # --------------------------------------------------------

    validate_territory(
        db,
        distributor,
        data.state_id,
        data.zone_id,
        data.area_id,
    )

    # --------------------------------------------------------
    # Check email
    # --------------------------------------------------------

    existing_user = get_user_by_email(
        db,
        data.email,
    )

    if existing_user is not None:
        raise SalespersonServiceError(
            "A user with this email already exists"
        )

    # --------------------------------------------------------
    # Check mobile
    # --------------------------------------------------------

    existing_user_mobile = get_user_by_mobile(
        db,
        data.mobile,
    )

    if existing_user_mobile is not None:
        raise SalespersonServiceError(
            "A user with this mobile number already exists"
        )

    # --------------------------------------------------------
    # Check employee code
    # --------------------------------------------------------

    if data.employee_code is not None:

        existing_employee = (
            get_salesperson_by_employee_code(
                db,
                data.employee_code,
            )
        )

        if existing_employee is not None:
            raise SalespersonServiceError(
                "Employee code already exists"
            )

    # --------------------------------------------------------
    # Get role
    # --------------------------------------------------------

    role = get_salesperson_role(db)

    # --------------------------------------------------------
    # Generate salesperson code
    # --------------------------------------------------------

    salesperson_code = generate_salesperson_code(
        db,
        distributor,
    )

    # --------------------------------------------------------
    # Create user
    # --------------------------------------------------------

    user = User(
        id=uuid.uuid4(),
        role_id=role.id,
        email=data.email,
        mobile=data.mobile,
        password_hash=hash_password(
            data.password
        ),
        is_active=True,
    )

    # --------------------------------------------------------
    # Create salesperson
    # --------------------------------------------------------

    salesperson = Salesperson(
        id=uuid.uuid4(),
        salesperson_code=salesperson_code,
        employee_code=data.employee_code,
        name=data.name,
        mobile=data.mobile,
        email=data.email,
        distributor_id=data.distributor_id,
        state_id=data.state_id,
        zone_id=data.zone_id,
        area_id=data.area_id,
        joining_date=data.joining_date,
        user_id=user.id,
        is_active=True,
    )

    db.add(user)
    db.add(salesperson)

    AuditService.log(
        db,
        actor_id=current_user.id,
        action="SALESPERSON_CREATED",
        entity="salesperson",
        entity_id=salesperson.id,
        new_value={
            "salesperson_code": salesperson.salesperson_code,
            "employee_code": salesperson.employee_code,
            "name": salesperson.name,
            "mobile": salesperson.mobile,
            "email": salesperson.email,
            "distributor_id": str(salesperson.distributor_id),
            "state_id": str(salesperson.state_id),
            "zone_id": str(salesperson.zone_id),
            "area_id": str(salesperson.area_id),
            "joining_date": (
                salesperson.joining_date.isoformat()
                if salesperson.joining_date else None
            ),
            "is_active": salesperson.is_active,
        },
    )

    try:
        db.commit()
        db.refresh(salesperson)

    except Exception:
        db.rollback()
        raise

    return salesperson


# ============================================================
# LIST SALESPERSONS
# ============================================================

def list_salespersons(
    db: Session,
    current_user: User,
) -> list[Salesperson]:

    role = current_user.role

    if role is None:
        raise SalespersonServiceError(
            "User role not found"
        )

    # --------------------------------------------------------
    # Admins can see all
    # --------------------------------------------------------

    if role.name in {
        "SUPER ADMIN",
        "MASTER ADMIN",
    }:
        return get_salespersons(db)

    # --------------------------------------------------------
    # Distributor can see only own salespersons
    # --------------------------------------------------------

    if role.name == "DISTRIBUTOR":

        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if distributor is None:
            raise SalespersonServiceError(
                "Distributor profile not found"
            )

        return get_salespersons_by_distributor(
            db,
            distributor.id,
        )

    raise SalespersonServiceError(
        "You are not authorized to view salespersons"
    )


# ============================================================
# GET SALESPERSON
# ============================================================

def get_salesperson(
    db: Session,
    salesperson_id: UUID,
    current_user: User,
) -> Salesperson:

    salesperson = get_salesperson_by_id(
        db,
        salesperson_id,
    )

    if salesperson is None:
        raise SalespersonServiceError(
            "Salesperson not found"
        )

    role = current_user.role

    if role is None:
        raise SalespersonServiceError(
            "User role not found"
        )

    # --------------------------------------------------------
    # Admins can access any salesperson
    # --------------------------------------------------------

    if role.name in {
        "SUPER ADMIN",
        "MASTER ADMIN",
    }:
        return salesperson

    # --------------------------------------------------------
    # Distributor can access only own salesperson
    # --------------------------------------------------------

    if role.name == "DISTRIBUTOR":

        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if distributor is None:
            raise SalespersonServiceError(
                "Distributor profile not found"
            )

        if salesperson.distributor_id != distributor.id:
            raise SalespersonServiceError(
                "You are not authorized to access this salesperson"
            )

        return salesperson

    raise SalespersonServiceError(
        "You are not authorized to access this salesperson"
    )


# ============================================================
# UPDATE SALESPERSON
# ============================================================

def update_salesperson(
    db: Session,
    salesperson_id: UUID,
    data: SalespersonUpdate,
    current_user: User,
) -> Salesperson:

    salesperson = get_salesperson(
        db,
        salesperson_id,
        current_user,
    )

    update_data = data.model_dump(
        exclude_unset=True,
    )

    old_value = {
        field: getattr(salesperson, field)
        for field in update_data
    }

    # --------------------------------------------------------
    # Prevent clearing mandatory login fields
    # --------------------------------------------------------

    if (
        "email" in update_data
        and update_data["email"] is None
    ):
        raise SalespersonServiceError(
            "Salesperson email cannot be cleared"
        )

    if (
        "mobile" in update_data
        and update_data["mobile"] is None
    ):
        raise SalespersonServiceError(
            "Salesperson mobile cannot be cleared"
        )

    # --------------------------------------------------------
    # Validate territory if changed
    # --------------------------------------------------------

    distributor = validate_distributor(
        db,
        salesperson.distributor_id,
    )

    state_id = update_data.get(
        "state_id",
        salesperson.state_id,
    )

    zone_id = update_data.get(
        "zone_id",
        salesperson.zone_id,
    )

    area_id = update_data.get(
        "area_id",
        salesperson.area_id,
    )

    validate_territory(
        db,
        distributor,
        state_id,
        zone_id,
        area_id,
    )

    # --------------------------------------------------------
    # Check employee code
    # --------------------------------------------------------

    if "employee_code" in update_data:

        new_employee_code = update_data[
            "employee_code"
        ]

        if new_employee_code is not None:

            existing_employee = (
                get_salesperson_by_employee_code(
                    db,
                    new_employee_code,
                )
            )

            if (
                existing_employee is not None
                and existing_employee.id
                != salesperson.id
            ):
                raise SalespersonServiceError(
                    "Employee code already exists"
                )

    # --------------------------------------------------------
    # Check email
    # --------------------------------------------------------

    if "email" in update_data:

        existing_user = get_user_by_email(
            db,
            update_data["email"],
        )

        if (
            existing_user is not None
            and existing_user.id
            != salesperson.user_id
        ):
            raise SalespersonServiceError(
                "A user with this email already exists"
            )

    # --------------------------------------------------------
    # Check mobile
    # --------------------------------------------------------

    if "mobile" in update_data:

        existing_user = get_user_by_mobile(
            db,
            update_data["mobile"],
        )

        if (
            existing_user is not None
            and existing_user.id
            != salesperson.user_id
        ):
            raise SalespersonServiceError(
                "A user with this mobile number already exists"
            )

    # --------------------------------------------------------
    # Get linked user
    # --------------------------------------------------------

    user = db.scalar(
        select(User).where(
            User.id == salesperson.user_id
        )
    )

    # --------------------------------------------------------
    # Update salesperson
    # --------------------------------------------------------

    for field, value in update_data.items():
        setattr(
            salesperson,
            field,
            value,
        )

    # --------------------------------------------------------
    # Synchronize user account
    # --------------------------------------------------------

    if user is not None:

        if "email" in update_data:
            user.email = update_data["email"]

        if "mobile" in update_data:
            user.mobile = update_data["mobile"]

    # --------------------------------------------------------
    # Audit + Commit
    # --------------------------------------------------------

    AuditService.log(
        db,
        actor_id=current_user.id,
        action="SALESPERSON_UPDATED",
        entity="salesperson",
        entity_id=salesperson.id,
        old_value={
            key: (
                value.isoformat()
                if isinstance(value, date)
                else str(value)
                if isinstance(value, uuid.UUID)
                else value
            )
            for key, value in old_value.items()
        },
        new_value={
            key: (
                getattr(salesperson, key).isoformat()
                if isinstance(getattr(salesperson, key), date)
                else str(getattr(salesperson, key))
                if isinstance(getattr(salesperson, key), uuid.UUID)
                else getattr(salesperson, key)
            )
            for key in update_data
        },
    )

    try:
        db.commit()
        db.refresh(salesperson)

    except Exception:
        db.rollback()
        raise

    return salesperson


# ============================================================
# UPDATE STATUS
# ============================================================

def update_salesperson_status(
    db: Session,
    salesperson_id: UUID,
    is_active: bool,
    current_user: User,
) -> Salesperson:

    salesperson = get_salesperson(
        db,
        salesperson_id,
        current_user,
    )

    old_status = salesperson.is_active
    salesperson.is_active = is_active

    # --------------------------------------------------------
    # Synchronize login account
    # --------------------------------------------------------

    user = db.scalar(
        select(User).where(
            User.id == salesperson.user_id
        )
    )

    if user is not None:
        user.is_active = is_active

    # --------------------------------------------------------
    # Audit + Commit
    # --------------------------------------------------------

    AuditService.log(
        db,
        actor_id=current_user.id,
        action="SALESPERSON_STATUS_CHANGED",
        entity="salesperson",
        entity_id=salesperson.id,
        old_value={"is_active": old_status},
        new_value={"is_active": is_active},
    )

    try:
        db.commit()
        db.refresh(salesperson)

    except Exception:
        db.rollback()
        raise

    return salesperson