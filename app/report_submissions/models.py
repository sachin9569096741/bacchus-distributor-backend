import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReportSubmissionStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    DISTRIBUTOR_REVIEW = "DISTRIBUTOR_REVIEW"
    RETURNED = "RETURNED"
    DISTRIBUTOR_SUBMITTED = "DISTRIBUTOR_SUBMITTED"
    ADMIN_REVIEW = "ADMIN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReportSubmission(Base):
    __tablename__ = "report_submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    report_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------
    # HIERARCHY
    # ------------------------------------------------------------

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "sellers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    salesperson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "salespersons.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    distributor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "distributors.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------
    # REPORT INFORMATION
    # ------------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    report_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    reporting_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    reporting_to: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # ------------------------------------------------------------
    # UPLOADED DOCUMENT
    # ------------------------------------------------------------

    report_file_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    # ------------------------------------------------------------
    # WORKFLOW
    # ------------------------------------------------------------

    status: Mapped[ReportSubmissionStatus] = mapped_column(
        nullable=False,
        default=ReportSubmissionStatus.SUBMITTED,
        index=True,
    )

    submitted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    distributor_reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    admin_reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------
    # TIMESTAMPS
    # ------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )