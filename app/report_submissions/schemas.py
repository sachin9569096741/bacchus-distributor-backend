from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.report_submissions.models import ReportSubmissionStatus


class ReportSubmissionCreate(BaseModel):
    seller_id: UUID

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    report_type: str = Field(
        min_length=1,
        max_length=100,
    )

    reporting_from: date
    reporting_to: date

    report_file_url: str = Field(
        min_length=1,
        max_length=5000,
    )

    original_filename: str = Field(
        min_length=1,
        max_length=255,
    )

    file_type: str = Field(
        min_length=1,
        max_length=100,
    )

    file_size: int | None = Field(
        default=None,
        ge=0,
    )

    remarks: str | None = Field(
        default=None,
        max_length=2000,
    )


class ReportSubmissionReview(BaseModel):
    remarks: str | None = Field(
        default=None,
        max_length=2000,
    )


class ReportSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_code: str

    seller_id: UUID
    salesperson_id: UUID
    distributor_id: UUID

    title: str
    report_type: str

    reporting_from: date
    reporting_to: date

    report_file_url: str
    original_filename: str
    file_type: str
    file_size: int | None

    status: ReportSubmissionStatus

    submitted_by: UUID

    distributor_reviewed_by: UUID | None
    admin_reviewed_by: UUID | None

    remarks: str | None

    created_at: datetime
    updated_at: datetime