from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.sales.models import Sale, SaleItem


# ============================================================
# SALES
# ============================================================

def get_sale_by_id(
    db: Session,
    sale_id: UUID,
) -> Sale | None:

    return db.scalar(
        select(Sale)
        .where(Sale.id == sale_id)
    )


def get_sale_by_number(
    db: Session,
    sale_number: str,
) -> Sale | None:

    return db.scalar(
        select(Sale)
        .where(Sale.sale_number == sale_number)
    )


def get_sales_by_distributor(
    db: Session,
    distributor_id: UUID,
) -> list[Sale]:

    return list(
        db.scalars(
            select(Sale)
            .where(
                Sale.distributor_id == distributor_id
            )
            .order_by(Sale.sale_date.desc(), Sale.created_at.desc())
        ).all()
    )


def get_sales_by_salesperson(
    db: Session,
    salesperson_id: UUID,
) -> list[Sale]:

    return list(
        db.scalars(
            select(Sale)
            .where(
                Sale.salesperson_id == salesperson_id
            )
            .order_by(Sale.sale_date.desc(), Sale.created_at.desc())
        ).all()
    )


def get_sales_by_seller(
    db: Session,
    seller_id: UUID,
) -> list[Sale]:

    return list(
        db.scalars(
            select(Sale)
            .where(
                Sale.seller_id == seller_id
            )
            .order_by(Sale.sale_date.desc(), Sale.created_at.desc())
        ).all()
    )


def create_sale(
    db: Session,
    sale: Sale,
) -> Sale:

    db.add(sale)
    db.flush()

    return sale


def save_sale(
    db: Session,
    sale: Sale,
) -> Sale:

    db.add(sale)
    db.flush()

    return sale


# ============================================================
# SALE ITEMS
# ============================================================

def get_sale_item_by_id(
    db: Session,
    sale_item_id: UUID,
) -> SaleItem | None:

    return db.scalar(
        select(SaleItem)
        .where(SaleItem.id == sale_item_id)
    )


def get_sale_items(
    db: Session,
    sale_id: UUID,
) -> list[SaleItem]:

    return list(
        db.scalars(
            select(SaleItem)
            .where(
                SaleItem.sale_id == sale_id
            )
        ).all()
    )


def create_sale_item(
    db: Session,
    sale_item: SaleItem,
) -> SaleItem:

    db.add(sale_item)
    db.flush()

    return sale_item


# ============================================================
# PRODUCT SALES
# ============================================================

def get_sales_by_product(
    db: Session,
    product_id: UUID,
) -> list[Sale]:

    return list(
        db.scalars(
            select(Sale)
            .join(
                SaleItem,
                SaleItem.sale_id == Sale.id,
            )
            .where(
                SaleItem.product_id == product_id
            )
            .order_by(
                Sale.sale_date.desc(),
                Sale.created_at.desc(),
            )
        ).all()
    )


def get_sales_by_variant(
    db: Session,
    variant_id: UUID,
) -> list[Sale]:

    return list(
        db.scalars(
            select(Sale)
            .join(
                SaleItem,
                SaleItem.sale_id == Sale.id,
            )
            .where(
                SaleItem.variant_id == variant_id
            )
            .order_by(
                Sale.sale_date.desc(),
                Sale.created_at.desc(),
            )
        ).all()
    )