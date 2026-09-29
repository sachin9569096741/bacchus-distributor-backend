from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.permissions.dependencies import (
    require_permission,
    require_role,
    require_any_role,
)
from app.report_submissions.schemas import (
    ReportSubmissionCreate,
    ReportSubmissionResponse,
    ReportSubmissionReview,
)
from app.report_submissions.service import (
    ReportSubmissionService,
    ReportSubmissionServiceError,
)

router = APIRouter(
    prefix="/report-submissions",
    tags=["Report Submissions"],
)


def handle_service_error(exc: ReportSubmissionServiceError):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


# ---------------------------------------------------------
# CREATE REPORT
# Salesperson submits report on behalf of Seller
# ---------------------------------------------------------

@router.post(
    "",
    response_model=ReportSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission("report.view")),
    ],
)
def create_report_submission(
    payload: ReportSubmissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return ReportSubmissionService.create(
            db=db,
            seller_id=payload.seller_id,
            title=payload.title,
            report_type=payload.report_type,
            reporting_from=payload.reporting_from,
            reporting_to=payload.reporting_to,
            report_file_url=payload.report_file_url,
            original_filename=payload.original_filename,
            file_type=payload.file_type,
            file_size=payload.file_size,
            remarks=payload.remarks,
            current_user=current_user,
        )
    except ReportSubmissionServiceError as exc:
        handle_service_error(exc)


# ---------------------------------------------------------
# MY REPORTS
# ---------------------------------------------------------

@router.get(
    "/my",
    response_model=list[ReportSubmissionResponse],
    dependencies=[
        Depends(require_permission("report.view")),
    ],
)
def get_my_reports(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        from app.salespersons.repository import (
            get_salesperson_by_user_id,
        )

        salesperson = get_salesperson_by_user_id(
            db,
            current_user.id,
        )

        if not salesperson:
            raise ReportSubmissionServiceError(
                "Salesperson profile not found"
            )

        return ReportSubmissionService.list_by_salesperson(
            db,
            salesperson.id,
        )

    except ReportSubmissionServiceError as exc:
        handle_service_error(exc)


# ---------------------------------------------------------
# SELLER REPORTS
# ---------------------------------------------------------

@router.get(
    "/seller/{seller_id}",
    response_model=list[ReportSubmissionResponse],
    dependencies=[
        Depends(require_permission("report.view")),
    ],
)
def get_seller_reports(
    seller_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        reports = ReportSubmissionService.list_by_seller(
            db,
            seller_id,
        )

        # Scope check for salesperson
        from app.salespersons.repository import (
            get_salesperson_by_user_id,
        )

        salesperson = get_salesperson_by_user_id(
            db,
            current_user.id,
        )

        if salesperson:
            reports = [
                report
                for report in reports
                if report.salesperson_id == salesperson.id
            ]

        return reports

    except ReportSubmissionServiceError as exc:
        handle_service_error(exc)


# ---------------------------------------------------------
# DISTRIBUTOR REPORTS
# ---------------------------------------------------------

@router.get(
    "/distributor",
    response_model=list[ReportSubmissionResponse],
    dependencies=[
        Depends(require_permission("report.view")),
    ],
)
def get_distributor_reports(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        from app.distributors.repository import (
            get_distributor_by_user_id,
        )

        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if not distributor:
            raise ReportSubmissionServiceError(
                "Distributor profile not found"
            )

        return ReportSubmissionService.list_by_distributor(
            db,
            distributor.id,
        )

    except ReportSubmissionServiceError as exc:
        handle_service_error(exc)


# ---------------------------------------------------------
# DISTRIBUTOR PENDING REVIEW
# ---------------------------------------------------------

@router.get(
    "/distributor/pending",
    response_model=list[ReportSubmissionResponse],
    dependencies=[
        Depends(require_role("DISTRIBUTOR")),
        Depends(require_permission("report.view")),
    ],
)
def get_pending_distributor_reports(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        from app.distributors.repository import (
            get_distributor_by_user_id,
        )

        distributor = get_distributor_by_user_id(
            db,
            current_user.id,
        )

        if not distributor:
            raise ReportSubmissionServiceError(
                "Distributor profile not found"
            )

        return ReportSubmissionService.pending_distributor_reports(
            db,
            distributor.id,
        )

    except ReportSubmissionServiceError as exc:
        handle_service_error(exc)


# ---------------------------------------------------------
# DISTRIBUTOR APPROVE / SUBMIT TO ADMIN
# ---------------------------------------------------------

@router.post(
    "/{report_id}/distributor-submit",
    response_model=ReportSubmissionResponse,
    dependencies=[
        Depends(require_role("DISTRIBUTOR")),
        Depends(require_permission("report.view")),
    ],
)
def distributor_submit_report(
    report_id: UUID,
    payload: ReportSubmissionReview,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return ReportSubmissionService.distributor_review(
            db=db,
            report_id=report_id,
            current_user=current_user,
            remarks=payload.remarks,
        )

    except ReportSubmissionServiceError as exc:
        handle_service_error(exc)


# ---------------------------------------------------------
# DISTRIBUTOR RETURN REPORT
# ---------------------------------------------------------

@router.post(
    "/{report_id}/distributor-return",
    response_model=ReportSubmissionResponse,
    dependencies=[
        Depends(require_role("DISTRIBUTOR")),
        Depends(require_permission("report.view")),
    ],
)
def distributor_return_report(
    report_id: UUID,
    payload: ReportSubmissionReview,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return ReportSubmissionService.return_by_distributor(
            db=db,
            report_id=report_id,
            current_user=current_user,
            remarks=payload.remarks or "",
        )

    except ReportSubmissionServiceError as exc:
        handle_service_error(exc)


# ---------------------------------------------------------
# ADMIN PENDING REPORTS
# ---------------------------------------------------------

@router.get(
    "/admin/pending",
    response_model=list[ReportSubmissionResponse],
    dependencies=[
        Depends(require_any_role("SUPER ADMIN", "MASTER ADMIN")),
        Depends(require_permission("report.view")),
    ],
)
def get_pending_admin_reports(
    db: Session = Depends(get_db),
):
    try:
        return ReportSubmissionService.pending_admin_reports(db)

    except ReportSubmissionServiceError as exc:
        handle_service_error(exc)


# ---------------------------------------------------------
# ADMIN START REVIEW
# ---------------------------------------------------------

@router.post(
    "/{report_id}/admin-review",
    response_model=ReportSubmissionResponse,
    dependencies=[
        Depends(require_any_role("SUPER ADMIN", "MASTER ADMIN")),
        Depends(require_permission("report.view")),
    ],
)
def admin_review_report(
    report_id: UUID,
    payload: ReportSubmissionReview,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return ReportSubmissionService.admin_review(
            db=db,
            report_id=report_id,
            current_user=current_user,
            remarks=payload.remarks,
        )

    except ReportSubmissionServiceError as exc:
        handle_service_error(exc)


# ---------------------------------------------------------
# ADMIN APPROVE
# ---------------------------------------------------------

@router.post(
    "/{report_id}/approve",
    response_model=ReportSubmissionResponse,
    dependencies=[
        Depends(require_any_role("SUPER ADMIN", "MASTER ADMIN")),
        Depends(require_permission("report.view")),
    ],
)
def approve_report(
    report_id: UUID,
    payload: ReportSubmissionReview,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return ReportSubmissionService.approve(
            db=db,
            report_id=report_id,
            current_user=current_user,
            remarks=payload.remarks,
        )

    except ReportSubmissionServiceError as exc:
        handle_service_error(exc)


# ---------------------------------------------------------
# ADMIN REJECT
# ---------------------------------------------------------

@router.post(
    "/{report_id}/reject",
    response_model=ReportSubmissionResponse,
    dependencies=[
        Depends(require_any_role("SUPER ADMIN", "MASTER ADMIN")),
        Depends(require_permission("report.view")),
    ],
)
def reject_report(
    report_id: UUID,
    payload: ReportSubmissionReview,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return ReportSubmissionService.reject(
            db=db,
            report_id=report_id,
            current_user=current_user,
            remarks=payload.remarks or "",
        )

    except ReportSubmissionServiceError as exc:
        handle_service_error(exc)


# ---------------------------------------------------------
# GET SINGLE REPORT
# ---------------------------------------------------------

@router.get(
    "/{report_id}",
    response_model=ReportSubmissionResponse,
    dependencies=[
        Depends(require_permission("report.view")),
    ],
)
def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return ReportSubmissionService.get(
            db,
            report_id,
        )

    except ReportSubmissionServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )