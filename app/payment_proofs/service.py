from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.distributors.models import Distributor
from app.payment_proofs.models import PaymentProof, PaymentProofStatus
from app.payment_proofs.repository import (
    create_payment_proof,
    get_all_payment_proofs,
    get_payment_proof_by_code,
    get_payment_proof_by_id,
    get_payment_proof_by_payment_id,
    get_payment_proofs_by_distributor,
    get_payment_proofs_by_salesperson,
    get_payment_proofs_by_seller,
    get_pending_payment_proofs_by_distributor,
    save_payment_proof,
)
from app.salespersons.models import Salesperson
from app.sellers.models import Seller
from app.dues.service import DueService


class PaymentProofServiceError(Exception):
    pass


class PaymentProofNotFoundError(PaymentProofServiceError):
    pass


class PaymentProofValidationError(PaymentProofServiceError):
    pass


class PaymentProofScopeError(PaymentProofServiceError):
    pass


class PaymentProofAlreadyExistsError(PaymentProofServiceError):
    pass


class PaymentProofService:

    @staticmethod
    def _generate_payment_proof_code(
        distributor: Distributor,
    ) -> str:
        return (
            f"{distributor.distributor_code}-"
            f"PP-{uuid4().hex[:8].upper()}"
        )

    @staticmethod
    def _validate_amount(amount: Decimal) -> None:
        if amount <= 0:
            raise PaymentProofValidationError(
                "Payment proof amount must be greater than zero"
            )

    @staticmethod
    def _validate_seller(
        seller: Seller | None,
    ) -> Seller:
        if seller is None:
            raise PaymentProofValidationError(
                "Seller not found"
            )

        if not seller.is_active:
            raise PaymentProofValidationError(
                "Seller is inactive"
            )

        return seller

    @staticmethod
    def _validate_salesperson(
        salesperson: Salesperson | None,
    ) -> Salesperson:
        if salesperson is None:
            raise PaymentProofValidationError(
                "Salesperson not found"
            )

        if not salesperson.is_active:
            raise PaymentProofValidationError(
                "Salesperson is inactive"
            )

        return salesperson

    @staticmethod
    def _validate_distributor(
        distributor: Distributor | None,
    ) -> Distributor:
        if distributor is None:
            raise PaymentProofValidationError(
                "Distributor not found"
            )

        if not distributor.is_active:
            raise PaymentProofValidationError(
                "Distributor is inactive"
            )

        return distributor

    @staticmethod
    def create_payment_proof(
        db: Session,
        *,
        seller: Seller,
        salesperson: Salesperson,
        distributor: Distributor,
        amount: Decimal,
        payment_id: str,
        screenshot_url: str,
        payment_date,
        remarks: str | None,
        submitted_by: UUID,
    ) -> PaymentProof:

        PaymentProofService._validate_amount(amount)
        PaymentProofService._validate_seller(seller)
        PaymentProofService._validate_salesperson(salesperson)
        PaymentProofService._validate_distributor(distributor)

        if salesperson.distributor_id != distributor.id:
            raise PaymentProofValidationError(
                "Salesperson does not belong to distributor"
            )

        if seller.distributor_id != distributor.id:
            raise PaymentProofValidationError(
                "Seller does not belong to distributor"
            )

        if seller.salesperson_id != salesperson.id:
            raise PaymentProofValidationError(
                "Seller is not assigned to this salesperson"
            )

        if not payment_id.strip():
            raise PaymentProofValidationError(
                "Payment ID/UTR is required"
            )

        if not screenshot_url.strip():
            raise PaymentProofValidationError(
                "Payment screenshot is required"
            )

        existing = get_payment_proof_by_payment_id(
            db,
            payment_id.strip(),
        )

        if existing is not None:
            raise PaymentProofAlreadyExistsError(
                "A payment proof with this payment ID already exists"
            )

        payment_proof = PaymentProof(
            payment_proof_code=PaymentProofService._generate_payment_proof_code(
                distributor
            ),
            seller_id=seller.id,
            salesperson_id=salesperson.id,
            distributor_id=distributor.id,
            amount=amount,
            payment_id=payment_id.strip(),
            screenshot_url=screenshot_url.strip(),
            payment_date=payment_date,
            remarks=remarks,
            status=PaymentProofStatus.PENDING,
            submitted_by=submitted_by,
        )

        return create_payment_proof(db, payment_proof)

    @staticmethod
    def get_payment_proof(
        db: Session,
        payment_proof_id: UUID,
    ) -> PaymentProof:

        payment_proof = get_payment_proof_by_id(
            db,
            payment_proof_id,
        )

        if payment_proof is None:
            raise PaymentProofNotFoundError(
                "Payment proof not found"
            )

        return payment_proof

    @staticmethod
    def verify_payment_proof(
        db: Session,
        *,
        payment_proof_id: UUID,
        verified_by: UUID,
    ) -> PaymentProof:

        payment_proof = PaymentProofService.get_payment_proof(
            db,
            payment_proof_id,
        )

        if payment_proof.status != PaymentProofStatus.PENDING:
            raise PaymentProofValidationError(
                "Only pending payment proofs can be verified"
            )

        DueService.record_verified_payment(
            db,
            seller_id=payment_proof.seller_id,
            distributor_id=payment_proof.distributor_id,
            payment_proof_id=payment_proof.id,
            amount=payment_proof.amount,
            created_by=verified_by,
        )

        payment_proof.status = PaymentProofStatus.VERIFIED
        payment_proof.verified_by = verified_by
        payment_proof.verified_at = datetime.now(timezone.utc)
        payment_proof.rejection_reason = None

        return save_payment_proof(db, payment_proof)

    @staticmethod
    def reject_payment_proof(
        db: Session,
        *,
        payment_proof_id: UUID,
        rejected_by: UUID,
        rejection_reason: str,
    ) -> PaymentProof:

        payment_proof = PaymentProofService.get_payment_proof(
            db,
            payment_proof_id,
        )

        if payment_proof.status != PaymentProofStatus.PENDING:
            raise PaymentProofValidationError(
                "Only pending payment proofs can be rejected"
            )

        if not rejection_reason.strip():
            raise PaymentProofValidationError(
                "Rejection reason is required"
            )

        payment_proof.status = PaymentProofStatus.REJECTED
        payment_proof.verified_by = rejected_by
        payment_proof.verified_at = datetime.now(timezone.utc)
        payment_proof.rejection_reason = rejection_reason.strip()

        return save_payment_proof(db, payment_proof)

    @staticmethod
    def list_by_seller(
        db: Session,
        seller_id: UUID,
    ) -> list[PaymentProof]:
        return get_payment_proofs_by_seller(
            db,
            seller_id,
        )

    @staticmethod
    def list_by_salesperson(
        db: Session,
        salesperson_id: UUID,
    ) -> list[PaymentProof]:
        return get_payment_proofs_by_salesperson(
            db,
            salesperson_id,
        )

    @staticmethod
    def list_by_distributor(
        db: Session,
        distributor_id: UUID,
    ) -> list[PaymentProof]:
        return get_payment_proofs_by_distributor(
            db,
            distributor_id,
        )

    @staticmethod
    def list_pending_by_distributor(
        db: Session,
        distributor_id: UUID,
    ) -> list[PaymentProof]:
        return get_pending_payment_proofs_by_distributor(
            db,
            distributor_id,
        )

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[PaymentProof]:
        return get_all_payment_proofs(db)