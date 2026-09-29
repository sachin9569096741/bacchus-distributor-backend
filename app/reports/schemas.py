from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.payment_proofs.models import PaymentProofStatus
from app.stock_requests.models import StockRequestStatus


class ReportFilter(BaseModel):
    from_date: date | None = None
    to_date: date | None = None
    seller_id: UUID | None = None


class SalesReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sale_id: UUID
    sale_number: str
    sale_date: date

    distributor_id: UUID
    seller_id: UUID
    salesperson_id: UUID

    total_amount: Decimal
    remarks: str | None

    created_by: UUID
    created_at: datetime


class InventoryReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inventory_id: UUID
    distributor_id: UUID
    salesperson_id: UUID | None

    product_id: UUID
    variant_id: UUID | None

    quantity: Decimal
    updated_at: datetime


class StockRequestReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_code: str

    distributor_id: UUID
    salesperson_id: UUID

    status: StockRequestStatus

    remarks: str | None
    rejection_reason: str | None

    reviewed_by: UUID | None
    reviewed_at: datetime | None

    created_at: datetime
    updated_at: datetime


class DueReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    seller_id: UUID
    distributor_id: UUID

    entry_type: str
    amount: Decimal

    reference_id: UUID | None
    reference_type: str | None

    remarks: str | None

    created_by: UUID
    created_at: datetime


class PaymentProofReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payment_proof_code: str

    seller_id: UUID
    salesperson_id: UUID
    distributor_id: UUID

    amount: Decimal
    payment_id: str

    screenshot_url: str
    payment_date: date

    remarks: str | None

    status: PaymentProofStatus

    submitted_by: UUID
    verified_by: UUID | None
    verified_at: datetime | None

    rejection_reason: str | None

    created_at: datetime
    updated_at: datetime