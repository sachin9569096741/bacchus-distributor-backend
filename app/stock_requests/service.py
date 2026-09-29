from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.inventory.service import (
    InventoryService,
    InventoryServiceError,
)
from app.stock_requests.models import (
    StockRequest,
    StockRequestItem,
    StockRequestStatus,
)
from app.stock_requests.repository import (
    create_stock_request,
    create_stock_request_item,
    get_pending_stock_requests_by_distributor,
    get_stock_request_by_id,
    get_stock_request_by_code,
    get_stock_requests_by_distributor,
    get_stock_requests_by_salesperson,
    get_stock_request_items,
    save_stock_request,
)


class StockRequestServiceError(Exception):
    """Base exception for stock-request business errors."""


class StockRequestNotFoundError(StockRequestServiceError):
    pass


class StockRequestAlreadyProcessedError(StockRequestServiceError):
    pass


class StockRequestPermissionError(StockRequestServiceError):
    pass


class InvalidStockRequestError(StockRequestServiceError):
    pass


class StockRequestInventoryError(StockRequestServiceError):
    pass


class StockRequestService:

    # ========================================================
    # REQUEST CODE
    # ========================================================

    @staticmethod
    def _generate_request_code(
        distributor_code: str,
    ) -> str:
        return (
            f"{distributor_code}-SR-"
            f"{uuid4().hex[:8].upper()}"
        )

    # ========================================================
    # CREATE REQUEST
    # ========================================================

    @staticmethod
    def create_request(
        db: Session,
        *,
        salesperson_id: UUID,
        distributor_id: UUID,
        items: list[dict],
        remarks: str | None = None,
    ) -> StockRequest:

        if not items:
            raise InvalidStockRequestError(
                "At least one product is required."
            )

        # ----------------------------------------------------
        # Prevent duplicate product + variant combinations
        # inside the same request.
        # ----------------------------------------------------

        combinations: set[tuple[UUID, UUID | None]] = set()

        for item in items:
            product_id = item["product_id"]
            variant_id = item.get("variant_id")
            quantity = item["quantity"]

            if quantity <= 0:
                raise InvalidStockRequestError(
                    "Requested quantity must be greater than zero."
                )

            combination = (
                product_id,
                variant_id,
            )

            if combination in combinations:
                raise InvalidStockRequestError(
                    "The same product/variant cannot be requested "
                    "more than once in the same request."
                )

            combinations.add(combination)

        # ----------------------------------------------------
        # Generate unique request code
        # ----------------------------------------------------

        request_code = StockRequestService._generate_request_code(
            distributor_code=StockRequestService._get_distributor_code(
                db=db,
                distributor_id=distributor_id,
            )
        )

        # ----------------------------------------------------
        # Create request
        # ----------------------------------------------------

        stock_request = StockRequest(
            id=uuid4(),
            request_code=request_code,
            distributor_id=distributor_id,
            salesperson_id=salesperson_id,
            status=StockRequestStatus.PENDING,
            remarks=remarks,
        )

        create_stock_request(
            db=db,
            stock_request=stock_request,
        )

        # ----------------------------------------------------
        # Create items
        # ----------------------------------------------------

        for item in items:

            stock_request_item = StockRequestItem(
                id=uuid4(),
                stock_request_id=stock_request.id,
                product_id=item["product_id"],
                variant_id=item.get("variant_id"),
                quantity=item["quantity"],
            )

            create_stock_request_item(
                db=db,
                item=stock_request_item,
            )

        db.flush()

        return stock_request

    # ========================================================
    # INTERNAL DISTRIBUTOR CODE
    # ========================================================

    @staticmethod
    def _get_distributor_code(
        db: Session,
        distributor_id: UUID,
    ) -> str:

        from app.distributors.repository import (
            get_distributor_by_id,
        )

        distributor = get_distributor_by_id(
            db=db,
            distributor_id=distributor_id,
        )

        if distributor is None:
            raise InvalidStockRequestError(
                "Distributor not found."
            )

        if not distributor.is_active:
            raise InvalidStockRequestError(
                "Distributor is inactive."
            )

        return distributor.distributor_code

    # ========================================================
    # GET REQUEST
    # ========================================================

    @staticmethod
    def get_request(
        db: Session,
        stock_request_id: UUID,
    ) -> StockRequest:

        stock_request = get_stock_request_by_id(
            db=db,
            stock_request_id=stock_request_id,
        )

        if stock_request is None:
            raise StockRequestNotFoundError(
                "Stock request not found."
            )

        return stock_request

    # ========================================================
    # GET BY CODE
    # ========================================================

    @staticmethod
    def get_request_by_code(
        db: Session,
        request_code: str,
    ) -> StockRequest:

        stock_request = get_stock_request_by_code(
            db=db,
            request_code=request_code,
        )

        if stock_request is None:
            raise StockRequestNotFoundError(
                "Stock request not found."
            )

        return stock_request

    # ========================================================
    # SALESPERSON REQUESTS
    # ========================================================

    @staticmethod
    def list_salesperson_requests(
        db: Session,
        *,
        salesperson_id: UUID,
        status: StockRequestStatus | None = None,
    ) -> list[StockRequest]:

        return get_stock_requests_by_salesperson(
            db=db,
            salesperson_id=salesperson_id,
            status=status,
        )

    # ========================================================
    # DISTRIBUTOR REQUESTS
    # ========================================================

    @staticmethod
    def list_distributor_requests(
        db: Session,
        *,
        distributor_id: UUID,
        status: StockRequestStatus | None = None,
    ) -> list[StockRequest]:

        return get_stock_requests_by_distributor(
            db=db,
            distributor_id=distributor_id,
            status=status,
        )

    # ========================================================
    # PENDING REQUESTS
    # ========================================================

    @staticmethod
    def list_pending_requests(
        db: Session,
        *,
        distributor_id: UUID,
    ) -> list[StockRequest]:

        return get_pending_stock_requests_by_distributor(
            db=db,
            distributor_id=distributor_id,
        )

    # ========================================================
    # APPROVE REQUEST
    # ========================================================

    @staticmethod
    def approve_request(
        db: Session,
        *,
        stock_request_id: UUID,
        reviewed_by: UUID,
    ) -> StockRequest:

        stock_request = StockRequestService.get_request(
            db=db,
            stock_request_id=stock_request_id,
        )

        # ----------------------------------------------------
        # Only PENDING requests can be approved.
        # ----------------------------------------------------

        if stock_request.status != StockRequestStatus.PENDING:
            raise StockRequestAlreadyProcessedError(
                f"Stock request is already "
                f"{stock_request.status.value}."
            )

        items = get_stock_request_items(
            db=db,
            stock_request_id=stock_request.id,
        )

        if not items:
            raise InvalidStockRequestError(
                "Stock request contains no items."
            )

        # ----------------------------------------------------
        # Transfer every requested item.
        #
        # InventoryService handles:
        #
        # Distributor stock  - quantity
        # Salesperson stock   + quantity
        # Ledger entries      + transfer reference
        # ----------------------------------------------------

        try:

            for item in items:

                InventoryService.issue_stock_to_salesperson(
                    db=db,
                    distributor_id=stock_request.distributor_id,
                    salesperson_id=stock_request.salesperson_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    performed_by=reviewed_by,
                    variant_id=item.variant_id,
                    reference_id=stock_request.id,
                    remarks=(
                        f"Stock request "
                        f"{stock_request.request_code}"
                    ),
                )

        except InventoryServiceError as exc:

            raise StockRequestInventoryError(
                str(exc)
            ) from exc

        # ----------------------------------------------------
        # Update request
        # ----------------------------------------------------

        stock_request.status = StockRequestStatus.APPROVED
        stock_request.reviewed_by = reviewed_by
        stock_request.reviewed_at = datetime.now(timezone.utc)
        stock_request.rejection_reason = None

        save_stock_request(
            db=db,
            stock_request=stock_request,
        )

        db.flush()

        return stock_request

    # ========================================================
    # REJECT REQUEST
    # ========================================================

    @staticmethod
    def reject_request(
        db: Session,
        *,
        stock_request_id: UUID,
        reviewed_by: UUID,
        rejection_reason: str,
    ) -> StockRequest:

        if not rejection_reason.strip():
            raise InvalidStockRequestError(
                "Rejection reason is required."
            )

        stock_request = StockRequestService.get_request(
            db=db,
            stock_request_id=stock_request_id,
        )

        # ----------------------------------------------------
        # Only PENDING requests can be rejected.
        # ----------------------------------------------------

        if stock_request.status != StockRequestStatus.PENDING:
            raise StockRequestAlreadyProcessedError(
                f"Stock request is already "
                f"{stock_request.status.value}."
            )

        stock_request.status = StockRequestStatus.REJECTED
        stock_request.reviewed_by = reviewed_by
        stock_request.reviewed_at = datetime.now(timezone.utc)
        stock_request.rejection_reason = rejection_reason.strip()

        save_stock_request(
            db=db,
            stock_request=stock_request,
        )

        db.flush()

        return stock_request