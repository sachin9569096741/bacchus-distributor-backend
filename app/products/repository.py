from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.products.models import (
    Category,
    Product,
    ProductImage,
    ProductVariant,
)


# ============================================================
# CATEGORY
# ============================================================


def get_category_by_id(
    db: Session,
    category_id: UUID,
) -> Category | None:
    return db.scalar(
        select(Category).where(
            Category.id == category_id,
        )
    )


def get_category_by_name(
    db: Session,
    name: str,
) -> Category | None:
    return db.scalar(
        select(Category).where(
            Category.name == name,
        )
    )


def get_categories(
    db: Session,
) -> list[Category]:
    return list(
        db.scalars(
            select(Category)
            .order_by(Category.created_at.desc())
        ).all()
    )


# ============================================================
# PRODUCT
# ============================================================


def get_product_by_id(
    db: Session,
    product_id: UUID,
) -> Product | None:
    return db.scalar(
        select(Product).where(
            Product.id == product_id,
        )
    )


def get_product_by_sku(
    db: Session,
    sku: str,
) -> Product | None:
    return db.scalar(
        select(Product).where(
            Product.sku == sku,
        )
    )


def get_products(
    db: Session,
) -> list[Product]:
    return list(
        db.scalars(
            select(Product)
            .order_by(Product.created_at.desc())
        ).all()
    )


def get_active_products(
    db: Session,
) -> list[Product]:
    return list(
        db.scalars(
            select(Product)
            .where(Product.is_active.is_(True))
            .order_by(Product.created_at.desc())
        ).all()
    )


def get_products_by_category(
    db: Session,
    category_id: UUID,
) -> list[Product]:
    return list(
        db.scalars(
            select(Product)
            .where(
                Product.category_id == category_id,
            )
            .order_by(Product.created_at.desc())
        ).all()
    )


# ============================================================
# PRODUCT VARIANT
# ============================================================


def get_variant_by_id(
    db: Session,
    variant_id: UUID,
) -> ProductVariant | None:
    return db.scalar(
        select(ProductVariant).where(
            ProductVariant.id == variant_id,
        )
    )


def get_variant_by_sku(
    db: Session,
    sku: str,
) -> ProductVariant | None:
    return db.scalar(
        select(ProductVariant).where(
            ProductVariant.sku == sku,
        )
    )


def get_variants_by_product(
    db: Session,
    product_id: UUID,
) -> list[ProductVariant]:
    return list(
        db.scalars(
            select(ProductVariant)
            .where(
                ProductVariant.product_id == product_id,
            )
            .order_by(ProductVariant.created_at.asc())
        ).all()
    )


# ============================================================
# PRODUCT IMAGE
# ============================================================


def get_product_image_by_id(
    db: Session,
    image_id: UUID,
) -> ProductImage | None:
    return db.scalar(
        select(ProductImage).where(
            ProductImage.id == image_id,
        )
    )


def get_product_image_by_public_id(
    db: Session,
    public_id: str,
) -> ProductImage | None:
    return db.scalar(
        select(ProductImage).where(
            ProductImage.cloudinary_public_id == public_id,
        )
    )


def get_product_images(
    db: Session,
    product_id: UUID,
) -> list[ProductImage]:
    return list(
        db.scalars(
            select(ProductImage)
            .where(
                ProductImage.product_id == product_id,
                ProductImage.is_active.is_(True),
            )
            .order_by(
                ProductImage.sort_order.asc(),
                ProductImage.created_at.asc(),
            )
        ).all()
    )


def get_product_image_count(
    db: Session,
    product_id: UUID,
) -> int:
    images = db.scalars(
        select(ProductImage.id)
        .where(
            ProductImage.product_id == product_id,
            ProductImage.is_active.is_(True),
        )
    ).all()

    return len(images)


def get_primary_product_image(
    db: Session,
    product_id: UUID,
) -> ProductImage | None:
    return db.scalar(
        select(ProductImage)
        .where(
            ProductImage.product_id == product_id,
            ProductImage.is_primary.is_(True),
            ProductImage.is_active.is_(True),
        )
    )