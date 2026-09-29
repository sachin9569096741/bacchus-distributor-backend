from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.report_submissions.models import (
    ReportSubmission,
    ReportSubmissionStatus,
)


def get_report_by_id(
    db: Session,
    report_id: UUID,
) -> ReportSubmission | None:
    return db.scalar(
        select(ReportSubmission).where(
            ReportSubmission.id == report_id
        )
    )


def get_report_by_code(
    db: Session,
    report_code: str,
) -> ReportSubmission | None:
    return db.scalar(
        select(ReportSubmission).where(
            ReportSubmission.report_code == report_code
        )
    )


def get_reports_by_seller(
    db: Session,
    seller_id: UUID,
) -> list[ReportSubmission]:
    stmt = (
        select(ReportSubmission)
        .where(
            ReportSubmission.seller_id == seller_id
        )
        .order_by(
            ReportSubmission.created_at.desc()
        )
    )

    return list(db.scalars(stmt).all())


def get_reports_by_salesperson(
    db: Session,
    salesperson_id: UUID,
) -> list[ReportSubmission]:
    stmt = (
        select(ReportSubmission)
        .where(
            ReportSubmission.salesperson_id
            == salesperson_id
        )
        .order_by(
            ReportSubmission.created_at.desc()
        )
    )

    return list(db.scalars(stmt).all())


def get_reports_by_distributor(
    db: Session,
    distributor_id: UUID,
) -> list[ReportSubmission]:
    stmt = (
        select(ReportSubmission)
        .where(
            ReportSubmission.distributor_id
            == distributor_id
        )
        .order_by(
            ReportSubmission.created_at.desc()
        )
    )

    return list(db.scalars(stmt).all())


def get_reports_by_status(
    db: Session,
    status: ReportSubmissionStatus,
) -> list[ReportSubmission]:
    stmt = (
        select(ReportSubmission)
        .where(
            ReportSubmission.status == status
        )
        .order_by(
            ReportSubmission.created_at.desc()
        )
    )

    return list(db.scalars(stmt).all())


def get_pending_distributor_reports(
    db: Session,
    distributor_id: UUID,
) -> list[ReportSubmission]:
    stmt = (
        select(ReportSubmission)
        .where(
            ReportSubmission.distributor_id
            == distributor_id,
            ReportSubmission.status
            == ReportSubmissionStatus.DISTRIBUTOR_REVIEW,
        )
        .order_by(
            ReportSubmission.created_at.desc()
        )
    )

    return list(db.scalars(stmt).all())


def get_pending_admin_reports(
    db: Session,
) -> list[ReportSubmission]:
    stmt = (
        select(ReportSubmission)
        .where(
            ReportSubmission.status
            == ReportSubmissionStatus.ADMIN_REVIEW,
        )
        .order_by(
            ReportSubmission.created_at.desc()
        )
    )

    return list(db.scalars(stmt).all())


def get_all_reports(
    db: Session,
) -> list[ReportSubmission]:
    stmt = select(ReportSubmission).order_by(
        ReportSubmission.created_at.desc()
    )

    return list(db.scalars(stmt).all())


def create_report(
    db: Session,
    report: ReportSubmission,
) -> ReportSubmission:
    db.add(report)
    db.flush()

    return report


def save_report(
    db: Session,
    report: ReportSubmission,
) -> ReportSubmission:
    db.add(report)
    db.flush()

    return report