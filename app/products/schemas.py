from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# CATEGORY
# ============================================================


class CategoryCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class CategoryUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class CategoryStatusUpdate(BaseModel):
    is_active: bool


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    is_active: bool


# ============================================================
# PRODUCT
# ============================================================


class ProductCreate(BaseModel):
    sku: str = Field(
        min_length=1,
        max_length=100,
    )

    name: str = Field(
        min_length=2,
        max_length=255,
    )

    category_id: UUID

    brand: str | None = Field(
        default=None,
        max_length=150,
    )

    unit: str = Field(
        min_length=1,
        max_length=50,
    )

    pack_size: str | None = Field(
        default=None,
        max_length=100,
    )

    mrp: Decimal = Field(
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    selling_price: Decimal = Field(
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    distributor_price: Decimal = Field(
        ge=0,
        max_digits=14,
        decimal_places=2,
    )


class ProductUpdate(BaseModel):
    sku: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    category_id: UUID | None = None

    brand: str | None = Field(
        default=None,
        max_length=150,
    )

    unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    pack_size: str | None = Field(
        default=None,
        max_length=100,
    )

    mrp: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    selling_price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    distributor_price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )


class ProductStatusUpdate(BaseModel):
    is_active: bool


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    name: str
    category_id: UUID
    brand: str | None
    unit: str
    pack_size: str | None

    mrp: Decimal
    selling_price: Decimal
    distributor_price: Decimal

    is_active: bool


# ============================================================
# PRODUCT VARIANT
# ============================================================


class ProductVariantCreate(BaseModel):
    product_id: UUID

    sku: str = Field(
        min_length=1,
        max_length=100,
    )

    name: str = Field(
        min_length=1,
        max_length=150,
    )


class ProductVariantUpdate(BaseModel):
    sku: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )


class ProductVariantStatusUpdate(BaseModel):
    is_active: bool


class ProductVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    sku: str
    name: str
    is_active: bool


# ============================================================
# PRODUCT IMAGE — CLOUDINARY
# ============================================================


class ProductImageUploadSignatureResponse(BaseModel):
    """
    Credentials/signature required by the frontend to upload
    an image directly to Cloudinary.
    """

    cloud_name: str
    api_key: str
    timestamp: int
    signature: str
    folder: str


class ProductImageCreate(BaseModel):
    """
    Metadata submitted to Bacchus after the frontend has
    successfully uploaded the image to Cloudinary.
    """

    cloudinary_public_id: str = Field(
        min_length=1,
        max_length=255,
    )

    is_primary: bool = False

    sort_order: int = Field(
        default=0,
        ge=0,
    )


class ProductImageUpdate(BaseModel):
    is_primary: bool | None = None

    sort_order: int | None = Field(
        default=None,
        ge=0,
    )


class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    cloudinary_public_id: str
    cloudinary_resource_type: str
    is_primary: bool
    sort_order: int
    is_active: bool