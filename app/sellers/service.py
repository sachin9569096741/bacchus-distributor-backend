import uuid
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.audit.service import AuditService
from app.distributors.models import Distributor
from app.geography.models import Area, State, Zone
from app.roles.models import Role
from app.salespersons.models import Salesperson
from app.sellers.models import Seller
from app.sellers.repository import (
    get_area_by_id,
    get_distributor_by_id,
    get_salesperson_by_id,
    get_seller_by_code,
    get_seller_by_email,
    get_seller_by_id,
    get_seller_by_mobile,
    get_sellers,
    get_sellers_by_distributor,
    get_sellers_by_salesperson,
    get_state_by_id,
    get_zone_by_id,
)
from app.sellers.schemas import (
    SellerCreate,
    SellerStatusUpdate,
    SellerUpdate,
)
from app.users.models import User


class SellerServiceError(Exception):
    pass


# ---------------------------------------------------------------------------
# Role helpers
# ---------------------------------------------------------------------------

def _get_role(
    db: Session,
    role_name: str,
) -> Role:
    role = db.query(Role).filter(
        Role.name == role_name,
        Role.is_active.is_(True),
    ).first()

    if role is None:
        raise SellerServiceError(
            f"{role_name} role is not configured"
        )

    return role


# ---------------------------------------------------------------------------
# Scope validation
# ---------------------------------------------------------------------------

def _validate_distributor_scope(
    db: Session,
    current_user: User,
    distributor_id: UUID,
) -> Distributor:
    distributor = get_distributor_by_id(
        db,
        distributor_id,
    )

    if distributor is None:
        raise SellerServiceError(
            "Distributor not found"
        )

    if not distributor.is_active:
        raise SellerServiceError(
            "Distributor is inactive"
        )

    role_name = current_user.role.name

    if role_name in {"SUPER ADMIN", "MASTER ADMIN"}:
        return distributor

    if role_name == "DISTRIBUTOR":
        if distributor.user_id != current_user.id:
            raise SellerServiceError(
                "You do not have access to this distributor"
            )

        return distributor

    raise SellerServiceError(
        "You do not have access to this distributor"
    )


# ---------------------------------------------------------------------------
# Territory validation
# ---------------------------------------------------------------------------

def _validate_territory(
    db: Session,
    distributor: Distributor,
    state_id: UUID,
    zone_id: UUID,
    area_id: UUID,
) -> None:
    state = get_state_by_id(
        db,
        state_id,
    )

    if state is None:
        raise SellerServiceError(
            "State not found or inactive"
        )

    zone = get_zone_by_id(
        db,
        zone_id,
    )

    if zone is None:
        raise SellerServiceError(
            "Zone not found or inactive"
        )

    area = get_area_by_id(
        db,
        area_id,
    )

    if area is None:
        raise SellerServiceError(
            "Area not found or inactive"
        )

    # Zone must belong to the selected state.
    if zone.state_id != state.id:
        raise SellerServiceError(
            "Zone does not belong to the selected state"
        )

    # Area must belong to both selected state and zone.
    if area.state_id != state.id:
        raise SellerServiceError(
            "Area does not belong to the selected state"
        )

    if area.zone_id != zone.id:
        raise SellerServiceError(
            "Area does not belong to the selected zone"
        )

    # Seller territory must match distributor territory.
    if distributor.state_id != state.id:
        raise SellerServiceError(
            "Seller state does not match distributor state"
        )

    if distributor.zone_id != zone.id:
        raise SellerServiceError(
            "Seller zone does not match distributor zone"
        )

    if distributor.area_id != area.id:
        raise SellerServiceError(
            "Seller area does not match distributor area"
        )


# ---------------------------------------------------------------------------
# Salesperson validation
# ---------------------------------------------------------------------------

def _validate_salesperson(
    db: Session,
    salesperson_id: UUID,
    distributor_id: UUID,
) -> Salesperson:
    salesperson = get_salesperson_by_id(
        db,
        salesperson_id,
    )

    if salesperson is None:
        raise SellerServiceError(
            "Salesperson not found"
        )

    if not salesperson.is_active:
        raise SellerServiceError(
            "Salesperson is inactive"
        )

    # A salesperson can only manage sellers belonging
    # to their own distributor.
    if salesperson.distributor_id != distributor_id:
        raise SellerServiceError(
            "Salesperson does not belong to the selected distributor"
        )

    return salesperson


# ---------------------------------------------------------------------------
# Seller code
# ---------------------------------------------------------------------------

def _generate_seller_code(
    db: Session,
    distributor: Distributor,
) -> str:
    """
    Generate a unique seller business code.

    Example:
        BAC-UP-WUP-GZB-D845F3F73-SL-A12B4C8D
    """

    for _ in range(10):
        random_part = uuid.uuid4().hex[:8].upper()

        seller_code = (
            f"{distributor.distributor_code}"
            f"-SL-{random_part}"
        )

        if get_seller_by_code(
            db,
            seller_code,
        ) is None:
            return seller_code

    raise SellerServiceError(
        "Unable to generate a unique seller code"
    )


# ---------------------------------------------------------------------------
# Create seller
# ---------------------------------------------------------------------------

def create_seller(
    db: Session,
    data: SellerCreate,
    current_user: User,
) -> Seller:
    distributor = _validate_distributor_scope(
        db,
        current_user,
        data.distributor_id,
    )

    _validate_territory(
        db,
        distributor,
        data.state_id,
        data.zone_id,
        data.area_id,
    )

    _validate_salesperson(
        db,
        data.salesperson_id,
        data.distributor_id,
    )

    if get_seller_by_mobile(
        db,
        data.mobile,
    ) is not None:
        raise SellerServiceError(
            "Seller with this mobile already exists"
        )

    if data.email is not None:
        if get_seller_by_email(
            db,
            str(data.email),
        ) is not None:
            raise SellerServiceError(
                "Seller with this email already exists"
            )

    seller_code = _generate_seller_code(
        db,
        distributor,
    )

    seller = Seller(
        seller_code=seller_code,
        business_name=data.business_name,
        owner_name=data.owner_name,
        mobile=data.mobile,
        email=str(data.email) if data.email else None,
        address=data.address,
        state_id=data.state_id,
        zone_id=data.zone_id,
        area_id=data.area_id,
        distributor_id=data.distributor_id,
        salesperson_id=data.salesperson_id,
        gst_number=data.gst_number,
        credit_limit=data.credit_limit,
        is_active=True,
    )

    db.add(seller)

    AuditService.log(
        db,
        actor_id=current_user.id,
        action="SELLER_CREATED",
        entity="seller",
        entity_id=seller.id,
        new_value={
            "seller_code": seller.seller_code,
            "business_name": seller.business_name,
            "owner_name": seller.owner_name,
            "mobile": seller.mobile,
            "email": seller.email,
            "address": seller.address,
            "state_id": str(seller.state_id),
            "zone_id": str(seller.zone_id),
            "area_id": str(seller.area_id),
            "distributor_id": str(seller.distributor_id),
            "salesperson_id": str(seller.salesperson_id),
            "gst_number": seller.gst_number,
            "credit_limit": str(seller.credit_limit),
            "is_active": seller.is_active,
        },
    )

    db.commit()
    db.refresh(seller)

    return seller


# ---------------------------------------------------------------------------
# List sellers
# ---------------------------------------------------------------------------

def list_sellers(
    db: Session,
    current_user: User,
) -> list[Seller]:
    role_name = current_user.role.name

    if role_name in {"SUPER ADMIN", "MASTER ADMIN"}:
        return get_sellers(db)

    if role_name == "DISTRIBUTOR":
        distributor = db.query(Distributor).filter(
            Distributor.user_id == current_user.id
        ).first()

        if distributor is None:
            raise SellerServiceError(
                "Distributor profile not found"
            )

        return get_sellers_by_distributor(
            db,
            distributor.id,
        )

    if role_name == "SALESPERSON":
        salesperson = db.query(Salesperson).filter(
            Salesperson.user_id == current_user.id
        ).first()

        if salesperson is None:
            raise SellerServiceError(
                "Salesperson profile not found"
            )

        return get_sellers_by_salesperson(
            db,
            salesperson.id,
        )

    raise SellerServiceError(
        "You do not have access to sellers"
    )


# ---------------------------------------------------------------------------
# Get seller
# ---------------------------------------------------------------------------

def get_seller(
    db: Session,
    seller_id: UUID,
    current_user: User,
) -> Seller:
    seller = get_seller_by_id(
        db,
        seller_id,
    )

    if seller is None:
        raise SellerServiceError(
            "Seller not found"
        )

    role_name = current_user.role.name

    if role_name in {"SUPER ADMIN", "MASTER ADMIN"}:
        return seller

    if role_name == "DISTRIBUTOR":
        distributor = db.query(Distributor).filter(
            Distributor.user_id == current_user.id
        ).first()

        if distributor is None:
            raise SellerServiceError(
                "Distributor profile not found"
            )

        if seller.distributor_id != distributor.id:
            raise SellerServiceError(
                "You do not have access to this seller"
            )

        return seller

    if role_name == "SALESPERSON":
        salesperson = db.query(Salesperson).filter(
            Salesperson.user_id == current_user.id
        ).first()

        if salesperson is None:
            raise SellerServiceError(
                "Salesperson profile not found"
            )

        if seller.salesperson_id != salesperson.id:
            raise SellerServiceError(
                "You do not have access to this seller"
            )

        return seller

    raise SellerServiceError(
        "You do not have access to this seller"
    )


# ---------------------------------------------------------------------------
# Update seller
# ---------------------------------------------------------------------------

def update_seller(
    db: Session,
    seller_id: UUID,
    data: SellerUpdate,
    current_user: User,
) -> Seller:
    seller = get_seller(
        db,
        seller_id,
        current_user,
    )

    update_data = data.model_dump(
        exclude_unset=True,
    )

    old_value = {
        field: getattr(seller, field)
        for field in update_data
    }

    if not update_data:
        raise SellerServiceError(
            "No fields provided for update"
        )

    if "mobile" in update_data:
        if update_data["mobile"] is None:
            raise SellerServiceError(
                "Mobile cannot be null"
            )

        existing = get_seller_by_mobile(
            db,
            update_data["mobile"],
        )

        if existing is not None and existing.id != seller.id:
            raise SellerServiceError(
                "Seller with this mobile already exists"
            )

    if "email" in update_data:
        if update_data["email"] is not None:
            existing = get_seller_by_email(
                db,
                str(update_data["email"]),
            )

            if existing is not None and existing.id != seller.id:
                raise SellerServiceError(
                    "Seller with this email already exists"
                )

            update_data["email"] = str(
                update_data["email"]
            )

    # Determine the final territory after update.
    final_state_id = update_data.get(
        "state_id",
        seller.state_id,
    )

    final_zone_id = update_data.get(
        "zone_id",
        seller.zone_id,
    )

    final_area_id = update_data.get(
        "area_id",
        seller.area_id,
    )

    # Territory cannot be changed independently of
    # the seller's distributor.
    distributor = get_distributor_by_id(
        db,
        seller.distributor_id,
    )

    if distributor is None:
        raise SellerServiceError(
            "Seller distributor not found"
        )

    _validate_territory(
        db,
        distributor,
        final_state_id,
        final_zone_id,
        final_area_id,
    )

    for field, value in update_data.items():
        setattr(
            seller,
            field,
            value,
        )

    AuditService.log(
        db,
        actor_id=current_user.id,
        action="SELLER_UPDATED",
        entity="seller",
        entity_id=seller.id,
        old_value={
            key: (
                str(value)
                if isinstance(value, UUID)
                else value
            )
            for key, value in old_value.items()
        },
        new_value={
            key: (
                str(getattr(seller, key))
                if isinstance(getattr(seller, key), UUID)
                else getattr(seller, key)
            )
            for key in update_data
        },
    )

    db.commit()
    db.refresh(seller)

    return seller


# ---------------------------------------------------------------------------
# Update seller status
# ---------------------------------------------------------------------------

def update_seller_status(
    db: Session,
    seller_id: UUID,
    data: SellerStatusUpdate,
    current_user: User,
) -> Seller:
    seller = get_seller(
        db,
        seller_id,
        current_user,
    )

    old_status = seller.is_active
    seller.is_active = data.is_active

    AuditService.log(
        db,
        actor_id=current_user.id,
        action="SELLER_STATUS_CHANGED",
        entity="seller",
        entity_id=seller.id,
        old_value={"is_active": old_status},
        new_value={"is_active": data.is_active},
    )

    db.commit()
    db.refresh(seller)

    return seller