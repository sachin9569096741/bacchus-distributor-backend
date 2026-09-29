from datetime import datetime, timezone
from uuid import UUID

from cloudinary import uploader
from cloudinary.utils import api_sign_request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.products import repository
from app.products.models import (
    Category,
    Product,
    ProductImage,
    ProductVariant,
)
from app.products.schemas import (
    CategoryCreate,
    CategoryUpdate,
    ProductCreate,
    ProductImageCreate,
    ProductImageUpdate,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantUpdate,
)
from app.users.models import User


class ProductServiceError(Exception):
    """Raised when product domain validation fails."""


class ProductService:

    # ============================================================
    # COMMON HELPERS
    # ============================================================

    @staticmethod
    def _ensure_admin(current_user: User) -> None:
        """
        Product catalog management is restricted to:
        SUPER ADMIN and MASTER ADMIN.
        """

        if current_user.role.name not in {
            "SUPER ADMIN",
            "MASTER ADMIN",
        }:
            raise ProductServiceError(
                "Only SUPER ADMIN or MASTER ADMIN can manage products."
            )

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip()

    # ============================================================
    # CATEGORY
    # ============================================================

    @staticmethod
    def create_category(
        db: Session,
        data: CategoryCreate,
        current_user: User,
    ) -> Category:

        ProductService._ensure_admin(current_user)

        name = ProductService._normalize(data.name)

        existing = repository.get_category_by_name(
            db,
            name,
        )

        if existing:
            raise ProductServiceError(
                f"Category '{name}' already exists."
            )

        category = Category(
            name=name,
            description=(
                data.description.strip()
                if data.description
                else None
            ),
            is_active=True,
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        return category

    @staticmethod
    def list_categories(
        db: Session,
        current_user: User,
        include_inactive: bool = False,
    ) -> list[Category]:

        categories = repository.get_categories(db)

        is_admin = current_user.role.name in {
            "SUPER ADMIN",
            "MASTER ADMIN",
        }

        if include_inactive and is_admin:
            return categories

        return [
            category
            for category in categories
            if category.is_active
        ]

    @staticmethod
    def get_category(
        db: Session,
        category_id: UUID,
    ) -> Category:

        category = repository.get_category_by_id(
            db,
            category_id,
        )

        if not category:
            raise ProductServiceError(
                "Category not found."
            )

        return category

    @staticmethod
    def update_category(
        db: Session,
        category_id: UUID,
        data: CategoryUpdate,
        current_user: User,
    ) -> Category:

        ProductService._ensure_admin(current_user)

        category = ProductService.get_category(
            db,
            category_id,
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "name" in update_data:

            name = ProductService._normalize(
                update_data["name"]
            )

            existing = repository.get_category_by_name(
                db,
                name,
            )

            if existing and existing.id != category.id:
                raise ProductServiceError(
                    f"Category '{name}' already exists."
                )

            category.name = name

        if "description" in update_data:

            category.description = (
                update_data["description"].strip()
                if update_data["description"]
                else None
            )

        db.commit()
        db.refresh(category)

        return category

    @staticmethod
    def update_category_status(
        db: Session,
        category_id: UUID,
        is_active: bool,
        current_user: User,
    ) -> Category:

        ProductService._ensure_admin(current_user)

        category = ProductService.get_category(
            db,
            category_id,
        )

        category.is_active = is_active

        db.commit()
        db.refresh(category)

        return category

    # ============================================================
    # PRODUCT
    # ============================================================

    @staticmethod
    def create_product(
        db: Session,
        data: ProductCreate,
        current_user: User,
    ) -> Product:

        ProductService._ensure_admin(current_user)

        sku = ProductService._normalize(data.sku)

        existing = repository.get_product_by_sku(
            db,
            sku,
        )

        if existing:
            raise ProductServiceError(
                f"Product SKU '{sku}' already exists."
            )

        category = repository.get_category_by_id(
            db,
            data.category_id,
        )

        if not category:
            raise ProductServiceError(
                "Category not found."
            )

        if not category.is_active:
            raise ProductServiceError(
                "Cannot create product under an inactive category."
            )

        product = Product(
            sku=sku,
            name=ProductService._normalize(data.name),
            category_id=data.category_id,
            brand=(
                data.brand.strip()
                if data.brand
                else None
            ),
            unit=ProductService._normalize(data.unit),
            pack_size=(
                data.pack_size.strip()
                if data.pack_size
                else None
            ),
            mrp=data.mrp,
            selling_price=data.selling_price,
            distributor_price=data.distributor_price,
            is_active=True,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return product

    @staticmethod
    def list_products(
        db: Session,
        current_user: User,
    ) -> list[Product]:

        role_name = current_user.role.name

        if role_name in {
            "SUPER ADMIN",
            "MASTER ADMIN",
        }:
            return repository.get_products(db)

        return repository.get_active_products(db)

    @staticmethod
    def get_product(
        db: Session,
        product_id: UUID,
        current_user: User | None = None,
    ) -> Product:

        product = repository.get_product_by_id(
            db,
            product_id,
        )

        if not product:
            raise ProductServiceError(
                "Product not found."
            )

        if (
            current_user
            and current_user.role.name
            not in {
                "SUPER ADMIN",
                "MASTER ADMIN",
            }
            and not product.is_active
        ):
            raise ProductServiceError(
                "Product is inactive."
            )

        return product

    @staticmethod
    def update_product(
        db: Session,
        product_id: UUID,
        data: ProductUpdate,
        current_user: User,
    ) -> Product:

        ProductService._ensure_admin(current_user)

        product = ProductService.get_product(
            db,
            product_id,
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "sku" in update_data:

            sku = ProductService._normalize(
                update_data["sku"]
            )

            existing = repository.get_product_by_sku(
                db,
                sku,
            )

            if existing and existing.id != product.id:
                raise ProductServiceError(
                    f"Product SKU '{sku}' already exists."
                )

            product.sku = sku

        if "name" in update_data:

            product.name = ProductService._normalize(
                update_data["name"]
            )

        if "category_id" in update_data:

            category = repository.get_category_by_id(
                db,
                update_data["category_id"],
            )

            if not category:
                raise ProductServiceError(
                    "Category not found."
                )

            if not category.is_active:
                raise ProductServiceError(
                    "Cannot assign an inactive category."
                )

            product.category_id = category.id

        if "brand" in update_data:

            product.brand = (
                update_data["brand"].strip()
                if update_data["brand"]
                else None
            )

        if "unit" in update_data:

            product.unit = ProductService._normalize(
                update_data["unit"]
            )

        if "pack_size" in update_data:

            product.pack_size = (
                update_data["pack_size"].strip()
                if update_data["pack_size"]
                else None
            )

        if "mrp" in update_data:
            product.mrp = update_data["mrp"]

        if "selling_price" in update_data:
            product.selling_price = update_data[
                "selling_price"
            ]

        if "distributor_price" in update_data:
            product.distributor_price = update_data[
                "distributor_price"
            ]

        db.commit()
        db.refresh(product)

        return product

    @staticmethod
    def update_product_status(
        db: Session,
        product_id: UUID,
        is_active: bool,
        current_user: User,
    ) -> Product:

        ProductService._ensure_admin(current_user)

        product = ProductService.get_product(
            db,
            product_id,
        )

        product.is_active = is_active

        db.commit()
        db.refresh(product)

        return product

    # ============================================================
    # PRODUCT VARIANTS
    # ============================================================

    @staticmethod
    def create_variant(
        db: Session,
        data: ProductVariantCreate,
        current_user: User,
    ) -> ProductVariant:

        ProductService._ensure_admin(current_user)

        product = ProductService.get_product(
            db,
            data.product_id,
        )

        if not product.is_active:
            raise ProductServiceError(
                "Cannot create a variant for an inactive product."
            )

        sku = ProductService._normalize(data.sku)

        existing = repository.get_variant_by_sku(
            db,
            sku,
        )

        if existing:
            raise ProductServiceError(
                f"Variant SKU '{sku}' already exists."
            )

        variant = ProductVariant(
            product_id=product.id,
            sku=sku,
            name=ProductService._normalize(data.name),
            is_active=True,
        )

        db.add(variant)
        db.commit()
        db.refresh(variant)

        return variant

    @staticmethod
    def list_variants(
        db: Session,
        product_id: UUID,
        current_user: User | None = None,
    ) -> list[ProductVariant]:

        product = ProductService.get_product(
            db,
            product_id,
            current_user,
        )

        variants = repository.get_variants_by_product(
            db,
            product.id,
        )

        if (
            current_user
            and current_user.role.name
            not in {
                "SUPER ADMIN",
                "MASTER ADMIN",
            }
        ):
            return [
                variant
                for variant in variants
                if variant.is_active
            ]

        return variants

    @staticmethod
    def get_variant(
        db: Session,
        product_id: UUID,
        variant_id: UUID,
        current_user: User | None = None,
    ) -> ProductVariant:

        ProductService.get_product(
            db,
            product_id,
            current_user,
        )

        variant = repository.get_variant_by_id(
            db,
            variant_id,
        )

        if not variant:
            raise ProductServiceError(
                "Product variant not found."
            )

        if variant.product_id != product_id:
            raise ProductServiceError(
                "Variant does not belong to this product."
            )

        if (
            current_user
            and current_user.role.name
            not in {
                "SUPER ADMIN",
                "MASTER ADMIN",
            }
            and not variant.is_active
        ):
            raise ProductServiceError(
                "Product variant is inactive."
            )

        return variant

    @staticmethod
    def update_variant(
        db: Session,
        product_id: UUID,
        variant_id: UUID,
        data: ProductVariantUpdate,
        current_user: User,
    ) -> ProductVariant:

        ProductService._ensure_admin(current_user)

        variant = ProductService.get_variant(
            db,
            product_id,
            variant_id,
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "sku" in update_data:

            sku = ProductService._normalize(
                update_data["sku"]
            )

            existing = repository.get_variant_by_sku(
                db,
                sku,
            )

            if existing and existing.id != variant.id:
                raise ProductServiceError(
                    f"Variant SKU '{sku}' already exists."
                )

            variant.sku = sku

        if "name" in update_data:

            variant.name = ProductService._normalize(
                update_data["name"]
            )

        db.commit()
        db.refresh(variant)

        return variant

    @staticmethod
    def update_variant_status(
        db: Session,
        product_id: UUID,
        variant_id: UUID,
        is_active: bool,
        current_user: User,
    ) -> ProductVariant:

        ProductService._ensure_admin(current_user)

        variant = ProductService.get_variant(
            db,
            product_id,
            variant_id,
        )

        variant.is_active = is_active

        db.commit()
        db.refresh(variant)

        return variant

    # ============================================================
    # CLOUDINARY SIGNED UPLOAD
    # ============================================================

    @staticmethod
    def generate_image_upload_signature(
        db: Session,
        product_id: UUID,
        current_user: User,
    ) -> dict:

        ProductService._ensure_admin(current_user)

        product = ProductService.get_product(
            db,
            product_id,
        )

        if not product.is_active:
            raise ProductServiceError(
                "Cannot upload images to an inactive product."
            )

        image_count = repository.get_product_image_count(
            db,
            product.id,
        )

        if image_count >= 5:
            raise ProductServiceError(
                "A product can have a maximum of 5 active images."
            )

        timestamp = int(
            datetime.now(timezone.utc).timestamp()
        )

        folder = f"bacchus/products/{product.id}"

        upload_params = {
            "timestamp": timestamp,
            "folder": folder,
        }

        signature = api_sign_request(
            upload_params,
            settings.CLOUDINARY_API_SECRET,
        )

        return {
            "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
            "api_key": settings.CLOUDINARY_API_KEY,
            "timestamp": timestamp,
            "signature": signature,
            "folder": folder,
        }

    # ============================================================
    # REGISTER CLOUDINARY IMAGE
    # ============================================================

    @staticmethod
    def add_product_image(
        db: Session,
        product_id: UUID,
        data: ProductImageCreate,
        current_user: User,
    ) -> ProductImage:

        ProductService._ensure_admin(current_user)

        product = ProductService.get_product(
            db,
            product_id,
        )

        if not product.is_active:
            raise ProductServiceError(
                "Cannot add images to an inactive product."
            )

        image_count = repository.get_product_image_count(
            db,
            product.id,
        )

        if image_count >= 5:
            raise ProductServiceError(
                "A product can have a maximum of 5 active images."
            )

        public_id = ProductService._normalize(
            data.cloudinary_public_id
        )

        expected_folder = (
            f"bacchus/products/{product.id}/"
        )

        if not public_id.startswith(expected_folder):
            raise ProductServiceError(
                "Invalid Cloudinary public ID for this product."
            )

        existing = (
            repository.get_product_image_by_public_id(
                db,
                public_id,
            )
        )

        if existing:
            raise ProductServiceError(
                "This Cloudinary image is already registered."
            )

        is_primary = (
            data.is_primary
            or image_count == 0
        )

        if is_primary:

            existing_primary = (
                repository.get_primary_product_image(
                    db,
                    product.id,
                )
            )

            if existing_primary:
                existing_primary.is_primary = False

        image = ProductImage(
            product_id=product.id,
            cloudinary_public_id=public_id,
            cloudinary_resource_type="image",
            is_primary=is_primary,
            sort_order=data.sort_order,
            is_active=True,
        )

        db.add(image)
        db.commit()
        db.refresh(image)

        return image

    # ============================================================
    # DIRECT BACKEND IMAGE UPLOAD
    # ============================================================

    @staticmethod
    def upload_product_image(
        db: Session,
        product_id: UUID,
        file_bytes: bytes,
        filename: str,
        current_user: User,
        is_primary: bool = False,
        sort_order: int = 0,
    ) -> ProductImage:

        ProductService._ensure_admin(current_user)

        product = ProductService.get_product(
            db,
            product_id,
        )

        if not product.is_active:
            raise ProductServiceError(
                "Cannot upload images to an inactive product."
            )

        image_count = repository.get_product_image_count(
            db,
            product.id,
        )

        if image_count >= 5:
            raise ProductServiceError(
                "A product can have a maximum of 5 active images."
            )

        if not file_bytes:
            raise ProductServiceError(
                "Uploaded image is empty."
            )

        folder = f"bacchus/products/{product.id}"

        try:
            upload_result = uploader.upload(
                file_bytes,
                folder=folder,
                resource_type="image",
                use_filename=True,
                unique_filename=True,
                overwrite=False,
            )

        except Exception as exc:
            print("CLOUDINARY ERROR:", repr(exc))
            raise ProductServiceError(
                f"Cloudinary upload failed: {exc}"
            ) from exc

        public_id = upload_result.get("public_id")

        if not public_id:
            raise ProductServiceError(
                "Cloudinary did not return a public ID."
            )

        existing = (
            repository.get_product_image_by_public_id(
                db,
                public_id,
            )
        )

        if existing:
            raise ProductServiceError(
                "This Cloudinary image is already registered."
            )

        make_primary = (
            is_primary
            or image_count == 0
        )

        if make_primary:

            existing_primary = (
                repository.get_primary_product_image(
                    db,
                    product.id,
                )
            )

            if existing_primary:
                existing_primary.is_primary = False

        image = ProductImage(
            product_id=product.id,
            cloudinary_public_id=public_id,
            cloudinary_resource_type="image",
            is_primary=make_primary,
            sort_order=sort_order,
            is_active=True,
        )

        db.add(image)
        db.commit()
        db.refresh(image)

        return image

    # ============================================================
    # LIST PRODUCT IMAGES
    # ============================================================

    @staticmethod
    def list_product_images(
        db: Session,
        product_id: UUID,
        current_user: User | None = None,
    ) -> list[ProductImage]:

        ProductService.get_product(
            db,
            product_id,
            current_user,
        )

        return repository.get_product_images(
            db,
            product_id,
        )

    # ============================================================
    # UPDATE PRODUCT IMAGE
    # ============================================================

    @staticmethod
    def update_product_image(
        db: Session,
        product_id: UUID,
        image_id: UUID,
        data: ProductImageUpdate,
        current_user: User,
    ) -> ProductImage:

        ProductService._ensure_admin(current_user)

        image = repository.get_product_image_by_id(
            db,
            image_id,
        )

        if not image:
            raise ProductServiceError(
                "Product image not found."
            )

        if image.product_id != product_id:
            raise ProductServiceError(
                "Image does not belong to this product."
            )

        if not image.is_active:
            raise ProductServiceError(
                "Product image is inactive."
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "is_primary" in update_data:

            if update_data["is_primary"]:

                existing_primary = (
                    repository.get_primary_product_image(
                        db,
                        product_id,
                    )
                )

                if (
                    existing_primary
                    and existing_primary.id != image.id
                ):
                    existing_primary.is_primary = False

                image.is_primary = True

            else:
                image.is_primary = False

        if "sort_order" in update_data:
            image.sort_order = update_data[
                "sort_order"
            ]

        db.commit()
        db.refresh(image)

        return image

    # ============================================================
    # DELETE PRODUCT IMAGE
    # ============================================================

    @staticmethod
    def delete_product_image(
        db: Session,
        product_id: UUID,
        image_id: UUID,
        current_user: User,
    ) -> None:

        ProductService._ensure_admin(current_user)

        image = repository.get_product_image_by_id(
            db,
            image_id,
        )

        if not image:
            raise ProductServiceError(
                "Product image not found."
            )

        if image.product_id != product_id:
            raise ProductServiceError(
                "Image does not belong to this product."
            )

        if not image.is_active:
            raise ProductServiceError(
                "Product image is already inactive."
            )

        try:
            result = uploader.destroy(
                image.cloudinary_public_id,
                resource_type=image.cloudinary_resource_type,
                invalidate=True,
            )

        except Exception as exc:
            raise ProductServiceError(
                "Cloudinary image deletion failed."
            ) from exc

        result_status = result.get("result")

        if result_status not in {
            "ok",
            "not found",
        }:
            raise ProductServiceError(
                "Cloudinary image deletion failed."
            )

        db.delete(image)
        db.commit()