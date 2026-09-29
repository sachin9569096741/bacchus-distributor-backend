from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.stock_requests.models import (
    StockRequest,
    StockRequestItem,
    StockRequestStatus,
)


# ============================================================
# STOCK REQUEST
# ============================================================

def get_stock_request_by_id(
    db: Session,
    stock_request_id: UUID,
) -> StockRequest | None:
    return db.scalar(
        select(StockRequest)
        .where(StockRequest.id == stock_request_id)
    )


def get_stock_request_by_code(
    db: Session,
    request_code: str,
) -> StockRequest | None:
    return db.scalar(
        select(StockRequest)
        .where(StockRequest.request_code == request_code)
    )


def get_stock_requests_by_distributor(
    db: Session,
    distributor_id: UUID,
    status: StockRequestStatus | None = None,
) -> list[StockRequest]:

    stmt = (
        select(StockRequest)
        .where(
            StockRequest.distributor_id == distributor_id
        )
        .order_by(StockRequest.created_at.desc())
    )

    if status is not None:
        stmt = stmt.where(
            StockRequest.status == status
        )

    return list(db.scalars(stmt).all())


def get_stock_requests_by_salesperson(
    db: Session,
    salesperson_id: UUID,
    status: StockRequestStatus | None = None,
) -> list[StockRequest]:

    stmt = (
        select(StockRequest)
        .where(
            StockRequest.salesperson_id == salesperson_id
        )
        .order_by(StockRequest.created_at.desc())
    )

    if status is not None:
        stmt = stmt.where(
            StockRequest.status == status
        )

    return list(db.scalars(stmt).all())


def get_pending_stock_requests_by_distributor(
    db: Session,
    distributor_id: UUID,
) -> list[StockRequest]:

    return list(
        db.scalars(
            select(StockRequest)
            .where(
                StockRequest.distributor_id == distributor_id,
                StockRequest.status == StockRequestStatus.PENDING,
            )
            .order_by(StockRequest.created_at.asc())
        ).all()
    )


def create_stock_request(
    db: Session,
    stock_request: StockRequest,
) -> StockRequest:

    db.add(stock_request)
    db.flush()

    return stock_request


def save_stock_request(
    db: Session,
    stock_request: StockRequest,
) -> StockRequest:

    db.add(stock_request)
    db.flush()

    return stock_request


# ============================================================
# STOCK REQUEST ITEMS
# ============================================================

def get_stock_request_item_by_id(
    db: Session,
    item_id: UUID,
) -> StockRequestItem | None:

    return db.scalar(
        select(StockRequestItem)
        .where(StockRequestItem.id == item_id)
    )


def get_stock_request_items(
    db: Session,
    stock_request_id: UUID,
) -> list[StockRequestItem]:

    return list(
        db.scalars(
            select(StockRequestItem)
            .where(
                StockRequestItem.stock_request_id
                == stock_request_id
            )
        ).all()
    )


def create_stock_request_item(
    db: Session,
    item: StockRequestItem,
) -> StockRequestItem:

    db.add(item)
    db.flush()

    return item