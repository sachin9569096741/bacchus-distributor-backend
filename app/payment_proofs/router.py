from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.distributors.repository import get_distributor_by_user_id
from app.payment_proofs.schemas import (
    PaymentProofCreate,
    PaymentProofReject,
    PaymentProofResponse,
)
from app.payment_proofs.service import (
    PaymentProofAlreadyExistsError,
    PaymentProofNotFoundError,
    PaymentProofScopeError,
    PaymentProofService,
    PaymentProofServiceError,
    PaymentProofValidationError,
)
from app.permissions.dependencies import require_permission
from app.salespersons.repository import get_salesperson_by_user_id
from app.sellers.repository import get_seller_by_id
from app.users.models import User


router = APIRouter(
    prefix="/payment-proofs",
    tags=["Payment Proofs"],
)


# ------------------------------------------------------------------
# SUBMIT PAYMENT PROOF
# ------------------------------------------------------------------

@router.post(
    "",
    response_model=PaymentProofResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission("payment_proof.create"))
    ],
)
def create_payment_proof(
    payload: PaymentProofCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Salesperson submits payment proof for an assigned seller.
    Distributor and salesperson IDs are derived server-side.
    """

    salesperson = get_salesperson_by_user_id(
        db,
        current_user.id,
    )

    if salesperson is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user is not a salesperson",
        )

    if not salesperson.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Salesperson account is inactive",
        )

    seller = get_seller_by_id(
        db,
        payload.seller_id,
    )

    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found",
        )

    distributor = get_distributor_by_user_id(
        db,
        current_user.id,
    )

    # Salesperson does not own a user_id on distributor.
    # Therefore derive distributor from salesperson.
    if distributor is None:
        from app.distributors.repository import get_distributor_by_id

        distributor = get_distributor_by_id(
            db,
            salesperson.distributor_id,
        )

    if distributor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Distributor not found",
        )

    try:
        payment_proof = PaymentProofService.create_payment_proof(
            db,
            seller=seller,
            salesperson=salesperson,
            distributor=distributor,
            amount=payload.amount,
            payment_id=payload.payment_id,
            screenshot_url=payload.screenshot_url,
            payment_date=payload.payment_date,
            remarks=payload.remarks,
            submitted_by=current_user.id,
        )

        db.commit()
        db.refresh(payment_proof)

        return payment_proof

    except PaymentProofAlreadyExistsError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except PaymentProofValidationError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except PaymentProofServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ------------------------------------------------------------------
# MY PAYMENT PROOFS
# ------------------------------------------------------------------

@router.get(
    "/my",
    response_model=list[PaymentProofResponse],
    dependencies=[
        Depends(require_permission("payment_proof.view"))
    ],
)
def get_my_payment_proofs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    salesperson = get_salesperson_by_user_id(
        db,
        current_user.id,
    )

    if salesperson is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user is not a salesperson",
        )

    return PaymentProofService.list_by_salesperson(
        db,
        salesperson.id,
    )


# ------------------------------------------------------------------
# DISTRIBUTOR PAYMENT PROOFS
# ------------------------------------------------------------------

@router.get(
    "/distributor",
    response_model=list[PaymentProofResponse],
    dependencies=[
        Depends(require_permission("payment_proof.view"))
    ],
)
def get_distributor_payment_proofs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    distributor = get_distributor_by_user_id(
        db,
        current_user.id,
    )

    if distributor is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user is not a distributor",
        )

    return PaymentProofService.list_by_distributor(
        db,
        distributor.id,
    )


@router.get(
    "/distributor/pending",
    response_model=list[PaymentProofResponse],
    dependencies=[
        Depends(require_permission("payment_proof.view"))
    ],
)
def get_pending_distributor_payment_proofs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    distributor = get_distributor_by_user_id(
        db,
        current_user.id,
    )

    if distributor is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user is not a distributor",
        )

    return PaymentProofService.list_pending_by_distributor(
        db,
        distributor.id,
    )


# ------------------------------------------------------------------
# ADMIN / FINANCE — ALL PAYMENT PROOFS
# ------------------------------------------------------------------

@router.get(
    "/all",
    response_model=list[PaymentProofResponse],
    dependencies=[
        Depends(require_permission("payment_proof.view"))
    ],
)
def get_all_payment_proofs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_roles = {
        "SUPER ADMIN",
        "MASTER ADMIN",
        "FINANCE USER",
    }

    if current_user.role.name not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to all payment proofs",
        )

    return PaymentProofService.list_all(db)


# ------------------------------------------------------------------
# GET SINGLE PAYMENT PROOF
# ------------------------------------------------------------------

@router.get(
    "/{payment_proof_id}",
    response_model=PaymentProofResponse,
    dependencies=[
        Depends(require_permission("payment_proof.view"))
    ],
)
def get_payment_proof(
    payment_proof_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment_proof = PaymentProofService.get_payment_proof(
        db,
        payment_proof_id,
    )

    role_name = current_user.role.name

    # Master Admin / Super Admin / Finance can view globally.
    if role_name in {
        "SUPER ADMIN",
        "MASTER ADMIN",
        "FINANCE USER",
    }:
        return payment_proof

    # Distributor can only view own network.
    if role_name == "DISTRIBUTOR":
        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if (
            distributor is None
            or payment_proof.distributor_id != distributor.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Payment proof is outside your scope",
            )

        return payment_proof

    # Salesperson can only view own submissions.
    if role_name == "SALESPERSON":
        salesperson = get_salesperson_by_user_id(
            db,
            current_user.id,
        )

        if (
            salesperson is None
            or payment_proof.salesperson_id != salesperson.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Payment proof is outside your scope",
            )

        return payment_proof

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this payment proof",
    )


# ------------------------------------------------------------------
# VERIFY
# ------------------------------------------------------------------

@router.post(
    "/{payment_proof_id}/verify",
    response_model=PaymentProofResponse,
    dependencies=[
        Depends(require_permission("payment_proof.verify"))
    ],
)
def verify_payment_proof(
    payment_proof_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment_proof = PaymentProofService.get_payment_proof(
        db,
        payment_proof_id,
    )

    role_name = current_user.role.name

    # Distributor can verify only their own distributor proofs.
    if role_name == "DISTRIBUTOR":
        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if (
            distributor is None
            or payment_proof.distributor_id != distributor.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Payment proof is outside your scope",
            )

    elif role_name not in {
        "SUPER ADMIN",
        "MASTER ADMIN",
        "FINANCE USER",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot verify payment proofs",
        )

    try:
        verified = PaymentProofService.verify_payment_proof(
            db,
            payment_proof_id=payment_proof_id,
            verified_by=current_user.id,
        )

        db.commit()
        db.refresh(verified)

        return verified

    except PaymentProofValidationError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except PaymentProofNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except PaymentProofServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ------------------------------------------------------------------
# REJECT
# ------------------------------------------------------------------

@router.post(
    "/{payment_proof_id}/reject",
    response_model=PaymentProofResponse,
    dependencies=[
        Depends(require_permission("payment_proof.reject"))
    ],
)
def reject_payment_proof(
    payment_proof_id: UUID,
    payload: PaymentProofReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment_proof = PaymentProofService.get_payment_proof(
        db,
        payment_proof_id,
    )

    role_name = current_user.role.name

    # Distributor can reject only their own distributor proofs.
    if role_name == "DISTRIBUTOR":
        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if (
            distributor is None
            or payment_proof.distributor_id != distributor.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Payment proof is outside your scope",
            )

    elif role_name not in {
        "SUPER ADMIN",
        "MASTER ADMIN",
        "FINANCE USER",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot reject payment proofs",
        )

    try:
        rejected = PaymentProofService.reject_payment_proof(
            db,
            payment_proof_id=payment_proof_id,
            rejected_by=current_user.id,
            rejection_reason=payload.rejection_reason,
        )

        db.commit()
        db.refresh(rejected)

        return rejected

    except PaymentProofValidationError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except PaymentProofNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except PaymentProofServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc