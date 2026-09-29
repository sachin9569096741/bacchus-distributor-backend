from datetime import datetime, timezone
from uuid import UUID
import secrets

from sqlalchemy.orm import Session

from app.report_submissions.models import (
    ReportSubmission,
    ReportSubmissionStatus,
)
from app.report_submissions.repository import (
    create_report,
    get_all_reports,
    get_pending_admin_reports,
    get_pending_distributor_reports,
    get_report_by_code,
    get_report_by_id,
    get_reports_by_distributor,
    get_reports_by_salesperson,
    get_reports_by_seller,
    save_report,
)
from app.sellers.repository import (
    get_seller_by_id,
)
from app.salespersons.repository import (
    get_salesperson_by_id,
)
from app.distributors.repository import (
    get_distributor_by_id,
)


class ReportSubmissionServiceError(Exception):
    pass


class ReportSubmissionService:

    @staticmethod
    def _generate_report_code() -> str:
        return f"RPT-{secrets.token_hex(5).upper()}"

    @staticmethod
    def _validate_reporting_period(
        reporting_from,
        reporting_to,
    ) -> None:
        if reporting_from > reporting_to:
            raise ReportSubmissionServiceError(
                "Reporting start date cannot be after reporting end date"
            )

    @staticmethod
    def _validate_seller_scope(
        db: Session,
        seller,
        salesperson,
    ) -> None:
        if not seller:
            raise ReportSubmissionServiceError(
                "Seller not found"
            )

        if not seller.is_active:
            raise ReportSubmissionServiceError(
                "Seller is inactive"
            )

        if not salesperson:
            raise ReportSubmissionServiceError(
                "Salesperson not found"
            )

        if not salesperson.is_active:
            raise ReportSubmissionServiceError(
                "Salesperson is inactive"
            )

        if seller.salesperson_id != salesperson.id:
            raise ReportSubmissionServiceError(
                "Seller is not assigned to this salesperson"
            )

        if seller.distributor_id != salesperson.distributor_id:
            raise ReportSubmissionServiceError(
                "Seller does not belong to salesperson's distributor"
            )

    @staticmethod
    def create(
        db: Session,
        *,
        seller_id: UUID,
        title: str,
        report_type: str,
        reporting_from,
        reporting_to,
        report_file_url: str,
        original_filename: str,
        file_type: str,
        file_size: int | None,
        remarks: str | None,
        current_user,
    ) -> ReportSubmission:

        ReportSubmissionService._validate_reporting_period(
            reporting_from,
            reporting_to,
        )

        seller = get_seller_by_id(db, seller_id)

        if not seller:
            raise ReportSubmissionServiceError(
                "Seller not found"
            )

        salesperson = get_salesperson_by_id(
            db,
            current_user.salesperson_id
            if hasattr(current_user, "salesperson_id")
            else None,
        )

        # Resolve salesperson through the authenticated user's account.
        if not salesperson:
            from app.salespersons.repository import (
                get_salesperson_by_user_id,
            )

            salesperson = get_salesperson_by_user_id(
                db,
                current_user.id,
            )

        ReportSubmissionService._validate_seller_scope(
            db,
            seller,
            salesperson,
        )

        distributor = get_distributor_by_id(
            db,
            seller.distributor_id,
        )

        if not distributor:
            raise ReportSubmissionServiceError(
                "Distributor not found"
            )

        report = ReportSubmission(
            report_code=ReportSubmissionService._generate_report_code(),
            seller_id=seller.id,
            salesperson_id=salesperson.id,
            distributor_id=distributor.id,
            title=title,
            report_type=report_type,
            reporting_from=reporting_from,
            reporting_to=reporting_to,
            report_file_url=report_file_url,
            original_filename=original_filename,
            file_type=file_type,
            file_size=file_size,
            status=ReportSubmissionStatus.DISTRIBUTOR_REVIEW,
            submitted_by=current_user.id,
            remarks=remarks,
        )

        create_report(db, report)

        return report

    @staticmethod
    def get(
        db: Session,
        report_id: UUID,
    ) -> ReportSubmission:

        report = get_report_by_id(db, report_id)

        if not report:
            raise ReportSubmissionServiceError(
                "Report submission not found"
            )

        return report

    @staticmethod
    def get_by_code(
        db: Session,
        report_code: str,
    ) -> ReportSubmission:

        report = get_report_by_code(db, report_code)

        if not report:
            raise ReportSubmissionServiceError(
                "Report submission not found"
            )

        return report

    @staticmethod
    def list_by_seller(
        db: Session,
        seller_id: UUID,
    ):
        return get_reports_by_seller(db, seller_id)

    @staticmethod
    def list_by_salesperson(
        db: Session,
        salesperson_id: UUID,
    ):
        return get_reports_by_salesperson(
            db,
            salesperson_id,
        )

    @staticmethod
    def list_by_distributor(
        db: Session,
        distributor_id: UUID,
    ):
        return get_reports_by_distributor(
            db,
            distributor_id,
        )

    @staticmethod
    def pending_distributor_reports(
        db: Session,
        distributor_id: UUID,
    ):
        return get_pending_distributor_reports(
            db,
            distributor_id,
        )

    @staticmethod
    def pending_admin_reports(
        db: Session,
    ):
        return get_pending_admin_reports(db)

    @staticmethod
    def list_all(
        db: Session,
    ):
        return get_all_reports(db)

    @staticmethod
    def distributor_review(
        db: Session,
        report_id: UUID,
        *,
        current_user,
        remarks: str | None = None,
    ) -> ReportSubmission:

        report = ReportSubmissionService.get(
            db,
            report_id,
        )

        if report.status != ReportSubmissionStatus.DISTRIBUTOR_REVIEW:
            raise ReportSubmissionServiceError(
                "Report is not pending distributor review"
            )

        distributor = get_distributor_by_id(
            db,
            report.distributor_id,
        )

        if not distributor:
            raise ReportSubmissionServiceError(
                "Distributor not found"
            )

        if distributor.user_id != current_user.id:
            raise ReportSubmissionServiceError(
                "You are not authorized to review this report"
            )

        report.status = ReportSubmissionStatus.DISTRIBUTOR_SUBMITTED
        report.distributor_reviewed_by = current_user.id

        if remarks is not None:
            report.remarks = remarks

        report.updated_at = datetime.now(timezone.utc)

        save_report(db, report)

        return report

    @staticmethod
    def return_by_distributor(
        db: Session,
        report_id: UUID,
        *,
        current_user,
        remarks: str,
    ) -> ReportSubmission:

        if not remarks.strip():
            raise ReportSubmissionServiceError(
                "Return remarks are required"
            )

        report = ReportSubmissionService.get(
            db,
            report_id,
        )

        if report.status != ReportSubmissionStatus.DISTRIBUTOR_REVIEW:
            raise ReportSubmissionServiceError(
                "Report is not pending distributor review"
            )

        distributor = get_distributor_by_id(
            db,
            report.distributor_id,
        )

        if not distributor or distributor.user_id != current_user.id:
            raise ReportSubmissionServiceError(
                "You are not authorized to return this report"
            )

        report.status = ReportSubmissionStatus.RETURNED
        report.distributor_reviewed_by = current_user.id
        report.remarks = remarks
        report.updated_at = datetime.now(timezone.utc)

        save_report(db, report)

        return report

    @staticmethod
    def admin_review(
        db: Session,
        report_id: UUID,
        *,
        current_user,
        remarks: str | None = None,
    ) -> ReportSubmission:

        report = ReportSubmissionService.get(
            db,
            report_id,
        )

        if report.status != ReportSubmissionStatus.DISTRIBUTOR_SUBMITTED:
            raise ReportSubmissionServiceError(
                "Report is not submitted for admin review"
            )

        report.status = ReportSubmissionStatus.ADMIN_REVIEW
        report.admin_reviewed_by = current_user.id

        if remarks is not None:
            report.remarks = remarks

        report.updated_at = datetime.now(timezone.utc)

        save_report(db, report)

        return report

    @staticmethod
    def approve(
        db: Session,
        report_id: UUID,
        *,
        current_user,
        remarks: str | None = None,
    ) -> ReportSubmission:

        report = ReportSubmissionService.get(
            db,
            report_id,
        )

        if report.status != ReportSubmissionStatus.ADMIN_REVIEW:
            raise ReportSubmissionServiceError(
                "Report is not pending admin review"
            )

        report.status = ReportSubmissionStatus.APPROVED
        report.admin_reviewed_by = current_user.id

        if remarks is not None:
            report.remarks = remarks

        report.updated_at = datetime.now(timezone.utc)

        save_report(db, report)

        return report

    @staticmethod
    def reject(
        db: Session,
        report_id: UUID,
        *,
        current_user,
        remarks: str,
    ) -> ReportSubmission:

        if not remarks.strip():
            raise ReportSubmissionServiceError(
                "Rejection remarks are required"
            )

        report = ReportSubmissionService.get(
            db,
            report_id,
        )

        if report.status != ReportSubmissionStatus.ADMIN_REVIEW:
            raise ReportSubmissionServiceError(
                "Report is not pending admin review"
            )

        report.status = ReportSubmissionStatus.REJECTED
        report.admin_reviewed_by = current_user.id
        report.remarks = remarks
        report.updated_at = datetime.now(timezone.utc)

        save_report(db, report)

        return report