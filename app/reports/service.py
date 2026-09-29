from datetime import date, datetime, time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dues.models import DueLedger
from app.inventory.models import Inventory
from app.payment_proofs.models import PaymentProof
from app.reports.schemas import (
    DueReportItem,
    InventoryReportItem,
    PaymentProofReportItem,
    SalesReportItem,
    StockRequestReportItem,
)
from app.sales.models import Sale
from app.stock_requests.models import StockRequest


class ReportService:

    # ============================================================
    # DATE HELPERS
    # ============================================================

    @staticmethod
    def _validate_dates(
        from_date: date | None,
        to_date: date | None,
    ) -> None:
        if from_date and to_date and from_date > to_date:
            raise ValueError(
                "from_date cannot be greater than to_date"
            )

    @staticmethod
    def _datetime_start(value: date) -> datetime:
        return datetime.combine(value, time.min)

    @staticmethod
    def _datetime_end(value: date) -> datetime:
        return datetime.combine(value, time.max)

    # ============================================================
    # SALES REPORT
    # ============================================================

    @staticmethod
    def get_sales_report(
        db: Session,
        *,
        distributor_id: UUID | None = None,
        seller_id: UUID | None = None,
        salesperson_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[SalesReportItem]:

        ReportService._validate_dates(
            from_date,
            to_date,
        )

        stmt = select(Sale).order_by(
            Sale.sale_date.desc(),
            Sale.created_at.desc(),
        )

        if distributor_id is not None:
            stmt = stmt.where(
                Sale.distributor_id == distributor_id
            )

        if seller_id is not None:
            stmt = stmt.where(
                Sale.seller_id == seller_id
            )

        if salesperson_id is not None:
            stmt = stmt.where(
                Sale.salesperson_id == salesperson_id
            )

        if from_date is not None:
            stmt = stmt.where(
                Sale.sale_date >= from_date
            )

        if to_date is not None:
            stmt = stmt.where(
                Sale.sale_date <= to_date
            )

        rows = db.scalars(stmt).all()

        return [
            SalesReportItem.model_validate(row)
            for row in rows
        ]

    # ============================================================
    # INVENTORY REPORT
    # ============================================================

    @staticmethod
    def get_inventory_report(
        db: Session,
        *,
        distributor_id: UUID | None = None,
        salesperson_id: UUID | None = None,
    ) -> list[InventoryReportItem]:

        stmt = select(Inventory).order_by(
            Inventory.updated_at.desc()
        )

        if distributor_id is not None:
            stmt = stmt.where(
                Inventory.distributor_id == distributor_id
            )

        if salesperson_id is not None:
            stmt = stmt.where(
                Inventory.salesperson_id == salesperson_id
            )

        rows = db.scalars(stmt).all()

        return [
            InventoryReportItem.model_validate(row)
            for row in rows
        ]

    # ============================================================
    # STOCK REQUEST REPORT
    # ============================================================

    @staticmethod
    def get_stock_request_report(
        db: Session,
        *,
        distributor_id: UUID | None = None,
        salesperson_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[StockRequestReportItem]:

        ReportService._validate_dates(
            from_date,
            to_date,
        )

        stmt = select(StockRequest).order_by(
            StockRequest.created_at.desc()
        )

        if distributor_id is not None:
            stmt = stmt.where(
                StockRequest.distributor_id
                == distributor_id
            )

        if salesperson_id is not None:
            stmt = stmt.where(
                StockRequest.salesperson_id
                == salesperson_id
            )

        if from_date is not None:
            stmt = stmt.where(
                StockRequest.created_at
                >= ReportService._datetime_start(from_date)
            )

        if to_date is not None:
            stmt = stmt.where(
                StockRequest.created_at
                <= ReportService._datetime_end(to_date)
            )

        rows = db.scalars(stmt).all()

        return [
            StockRequestReportItem.model_validate(row)
            for row in rows
        ]

    # ============================================================
    # DUE REPORT
    # ============================================================

    @staticmethod
    def get_due_report(
        db: Session,
        *,
        distributor_id: UUID | None = None,
        seller_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[DueReportItem]:

        ReportService._validate_dates(
            from_date,
            to_date,
        )

        stmt = select(DueLedger).order_by(
            DueLedger.created_at.desc()
        )

        if distributor_id is not None:
            stmt = stmt.where(
                DueLedger.distributor_id
                == distributor_id
            )

        if seller_id is not None:
            stmt = stmt.where(
                DueLedger.seller_id == seller_id
            )

        if from_date is not None:
            stmt = stmt.where(
                DueLedger.created_at
                >= ReportService._datetime_start(from_date)
            )

        if to_date is not None:
            stmt = stmt.where(
                DueLedger.created_at
                <= ReportService._datetime_end(to_date)
            )

        rows = db.scalars(stmt).all()

        return [
            DueReportItem.model_validate(row)
            for row in rows
        ]

    # ============================================================
    # PAYMENT PROOF REPORT
    # ============================================================

    @staticmethod
    def get_payment_proof_report(
        db: Session,
        *,
        distributor_id: UUID | None = None,
        seller_id: UUID | None = None,
        salesperson_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[PaymentProofReportItem]:

        ReportService._validate_dates(
            from_date,
            to_date,
        )

        stmt = select(PaymentProof).order_by(
            PaymentProof.created_at.desc()
        )

        if distributor_id is not None:
            stmt = stmt.where(
                PaymentProof.distributor_id
                == distributor_id
            )

        if seller_id is not None:
            stmt = stmt.where(
                PaymentProof.seller_id == seller_id
            )

        if salesperson_id is not None:
            stmt = stmt.where(
                PaymentProof.salesperson_id
                == salesperson_id
            )

        if from_date is not None:
            stmt = stmt.where(
                PaymentProof.payment_date
                >= from_date
            )

        if to_date is not None:
            stmt = stmt.where(
                PaymentProof.payment_date
                <= to_date
            )

        rows = db.scalars(stmt).all()

        return [
            PaymentProofReportItem.model_validate(row)
            for row in rows
        ]