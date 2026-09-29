from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.dues.models import DueEntryType, DueLedger
from app.dues.repository import (
    create_due_entry,
    get_due_entries_by_distributor,
    get_due_entries_by_seller,
    get_due_entry_by_id,
    get_due_entry_by_reference,
)
from app.distributors.repository import get_distributor_by_id
from app.sellers.repository import get_seller_by_id


class DueServiceError(Exception):
    pass


class DueNotFoundError(DueServiceError):
    pass


class DueValidationError(DueServiceError):
    pass


class DueScopeError(DueServiceError):
    pass


class DueAlreadyExistsError(DueServiceError):
    pass


class DueService:

    @staticmethod
    def _validate_amount(amount: Decimal) -> None:
        if amount <= 0:
            raise DueValidationError("Amount must be greater than zero.")

    @staticmethod
    def _validate_seller(
        db: Session,
        seller_id: UUID,
        distributor_id: UUID | None = None,
    ):
        seller = get_seller_by_id(db, seller_id)

        if not seller:
            raise DueValidationError("Seller not found.")

        if not seller.is_active:
            raise DueValidationError("Seller is inactive.")

        if distributor_id is not None and seller.distributor_id != distributor_id:
            raise DueScopeError(
                "Seller does not belong to the specified distributor."
            )

        return seller

    @staticmethod
    def _validate_distributor(
        db: Session,
        distributor_id: UUID,
    ):
        distributor = get_distributor_by_id(db, distributor_id)

        if not distributor:
            raise DueValidationError("Distributor not found.")

        if not distributor.is_active:
            raise DueValidationError("Distributor is inactive.")

        return distributor

    @classmethod
    def create_entry(
        cls,
        db: Session,
        *,
        seller_id: UUID,
        distributor_id: UUID,
        entry_type: DueEntryType,
        amount: Decimal,
        created_by: UUID,
        reference_id: UUID | None = None,
        reference_type: str | None = None,
        remarks: str | None = None,
    ) -> DueLedger:

        cls._validate_amount(amount)
        cls._validate_distributor(db, distributor_id)
        cls._validate_seller(
            db,
            seller_id,
            distributor_id,
        )

        if entry_type == DueEntryType.CREDIT_SALE:
            reference_type = reference_type or "SALE"

        elif entry_type == DueEntryType.VERIFIED_PAYMENT:
            reference_type = reference_type or "PAYMENT_PROOF"

        elif entry_type == DueEntryType.ADJUSTMENT:
            reference_type = reference_type or "ADJUSTMENT"

        if reference_id is not None:
            existing = get_due_entry_by_reference(
                db,
                reference_id,
                entry_type,
            )

            if existing:
                raise DueAlreadyExistsError(
                    "A due entry already exists for this reference."
                )

        due_entry = DueLedger(
            seller_id=seller_id,
            distributor_id=distributor_id,
            entry_type=entry_type,
            amount=amount,
            reference_id=reference_id,
            reference_type=reference_type,
            remarks=remarks,
            created_by=created_by,
        )

        return create_due_entry(db, due_entry)

    @classmethod
    def record_credit_sale(
        cls,
        db: Session,
        *,
        seller_id: UUID,
        distributor_id: UUID,
        sale_id: UUID,
        amount: Decimal,
        created_by: UUID,
        remarks: str | None = None,
    ) -> DueLedger:

        return cls.create_entry(
            db,
            seller_id=seller_id,
            distributor_id=distributor_id,
            entry_type=DueEntryType.CREDIT_SALE,
            amount=amount,
            created_by=created_by,
            reference_id=sale_id,
            reference_type="SALE",
            remarks=remarks,
        )

    @classmethod
    def record_verified_payment(
        cls,
        db: Session,
        *,
        seller_id: UUID,
        distributor_id: UUID,
        payment_proof_id: UUID,
        amount: Decimal,
        created_by: UUID,
        remarks: str | None = None,
    ) -> DueLedger:

        return cls.create_entry(
            db,
            seller_id=seller_id,
            distributor_id=distributor_id,
            entry_type=DueEntryType.VERIFIED_PAYMENT,
            amount=amount,
            created_by=created_by,
            reference_id=payment_proof_id,
            reference_type="PAYMENT_PROOF",
            remarks=remarks,
        )

    @classmethod
    def record_adjustment(
        cls,
        db: Session,
        *,
        seller_id: UUID,
        distributor_id: UUID,
        amount: Decimal,
        created_by: UUID,
        reference_id: UUID | None = None,
        remarks: str | None = None,
    ) -> DueLedger:

        return cls.create_entry(
            db,
            seller_id=seller_id,
            distributor_id=distributor_id,
            entry_type=DueEntryType.ADJUSTMENT,
            amount=amount,
            created_by=created_by,
            reference_id=reference_id,
            reference_type="ADJUSTMENT",
            remarks=remarks,
        )

    @classmethod
    def get_entry(
        cls,
        db: Session,
        due_id: UUID,
    ) -> DueLedger:

        entry = get_due_entry_by_id(db, due_id)

        if not entry:
            raise DueNotFoundError("Due entry not found.")

        return entry

    @staticmethod
    def list_seller_dues(
        db: Session,
        seller_id: UUID,
    ) -> list[DueLedger]:

        return get_due_entries_by_seller(
            db,
            seller_id,
        )

    @staticmethod
    def list_distributor_dues(
        db: Session,
        distributor_id: UUID,
    ) -> list[DueLedger]:

        return get_due_entries_by_distributor(
            db,
            distributor_id,
        )

    @classmethod
    def get_seller_outstanding(
        cls,
        db: Session,
        seller_id: UUID,
    ) -> Decimal:

        entries = get_due_entries_by_seller(
            db,
            seller_id,
        )

        outstanding = Decimal("0.00")

        for entry in entries:
            if entry.entry_type == DueEntryType.CREDIT_SALE:
                outstanding += entry.amount

            elif entry.entry_type == DueEntryType.VERIFIED_PAYMENT:
                outstanding -= entry.amount

            elif entry.entry_type == DueEntryType.ADJUSTMENT:
                outstanding += entry.amount

        return outstanding

    @classmethod
    def get_seller_summary(
        cls,
        db: Session,
        seller_id: UUID,
    ) -> dict:

        entries = get_due_entries_by_seller(
            db,
            seller_id,
        )

        total_credit_sales = Decimal("0.00")
        total_verified_payments = Decimal("0.00")
        total_adjustments = Decimal("0.00")

        for entry in entries:
            if entry.entry_type == DueEntryType.CREDIT_SALE:
                total_credit_sales += entry.amount

            elif entry.entry_type == DueEntryType.VERIFIED_PAYMENT:
                total_verified_payments += entry.amount

            elif entry.entry_type == DueEntryType.ADJUSTMENT:
                total_adjustments += entry.amount

        outstanding = (
            total_credit_sales
            - total_verified_payments
            + total_adjustments
        )

        return {
            "seller_id": seller_id,
            "distributor_id": entries[0].distributor_id if entries else None,
            "total_credit_sales": total_credit_sales,
            "total_verified_payments": total_verified_payments,
            "total_adjustments": total_adjustments,
            "outstanding": outstanding,
        }