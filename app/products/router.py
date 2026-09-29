from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    get_database,
)
from app.permissions.dependencies import require_permission
from app.products import service
from app.products.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryStatusUpdate,
    CategoryUpdate,
    ProductCreate,
    ProductImageCreate,
    ProductImageResponse,
    ProductImageUpdate,
    ProductImageUploadSignatureResponse,
    ProductResponse,
    ProductStatusUpdate,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantResponse,
    ProductVariantStatusUpdate,
    ProductVariantUpdate,
)
from app.users.models import User


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


# ============================================================
# ERROR HANDLER
# ============================================================

def _service_error(
    exc: service.ProductServiceError,
) -> HTTPException:

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


# ============================================================
# CATEGORY
# ============================================================

@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(
                "product.create"
            )
        )
    ],
)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.create_category(
            db=db,
            data=payload,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


@router.get(
    "/categories",
    response_model=list[CategoryResponse],
    dependencies=[
        Depends(
            require_permission(
                "product.view"
            )
        )
    ],
)
def list_categories(
    include_inactive: bool = False,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.list_categories(
            db=db,
            current_user=current_user,
            include_inactive=include_inactive,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


@router.get(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    dependencies=[
        Depends(
            require_permission(
                "product.view"
            )
        )
    ],
)
def get_category(
    category_id: UUID,
    db: Session = Depends(get_database),
):
    try:
        return service.ProductService.get_category(
            db=db,
            category_id=category_id,
        )

    except service.ProductServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    dependencies=[
        Depends(
            require_permission(
                "product.update"
            )
        )
    ],
)
def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.update_category(
            db=db,
            category_id=category_id,
            data=payload,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


@router.patch(
    "/categories/{category_id}/status",
    response_model=CategoryResponse,
    dependencies=[
        Depends(
            require_permission(
                "product.update"
            )
        )
    ],
)
def update_category_status(
    category_id: UUID,
    payload: CategoryStatusUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.update_category_status(
            db=db,
            category_id=category_id,
            is_active=payload.is_active,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


# ============================================================
# PRODUCT
# ============================================================

@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(
                "product.create"
            )
        )
    ],
)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.create_product(
            db=db,
            data=payload,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


@router.get(
    "",
    response_model=list[ProductResponse],
    dependencies=[
        Depends(
            require_permission(
                "product.view"
            )
        )
    ],
)
def list_products(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.list_products(
            db=db,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[
        Depends(
            require_permission(
                "product.view"
            )
        )
    ],
)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.get_product(
            db=db,
            product_id=product_id,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[
        Depends(
            require_permission(
                "product.update"
            )
        )
    ],
)
def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.update_product(
            db=db,
            product_id=product_id,
            data=payload,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


@router.patch(
    "/{product_id}/status",
    response_model=ProductResponse,
    dependencies=[
        Depends(
            require_permission(
                "product.update"
            )
        )
    ],
)
def update_product_status(
    product_id: UUID,
    payload: ProductStatusUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.update_product_status(
            db=db,
            product_id=product_id,
            is_active=payload.is_active,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


# ============================================================
# PRODUCT VARIANTS
# ============================================================

@router.post(
    "/{product_id}/variants",
    response_model=ProductVariantResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(
                "product.create"
            )
        )
    ],
)
def create_variant(
    product_id: UUID,
    payload: ProductVariantCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    if payload.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Payload product_id does not match "
                "URL product_id."
            ),
        )

    try:
        return service.ProductService.create_variant(
            db=db,
            data=payload,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


@router.get(
    "/{product_id}/variants",
    response_model=list[ProductVariantResponse],
    dependencies=[
        Depends(
            require_permission(
                "product.view"
            )
        )
    ],
)
def list_variants(
    product_id: UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.list_variants(
            db=db,
            product_id=product_id,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "/{product_id}/variants/{variant_id}",
    response_model=ProductVariantResponse,
    dependencies=[
        Depends(
            require_permission(
                "product.view"
            )
        )
    ],
)
def get_variant(
    product_id: UUID,
    variant_id: UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.get_variant(
            db=db,
            product_id=product_id,
            variant_id=variant_id,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch(
    "/{product_id}/variants/{variant_id}",
    response_model=ProductVariantResponse,
    dependencies=[
        Depends(
            require_permission(
                "product.update"
            )
        )
    ],
)
def update_variant(
    product_id: UUID,
    variant_id: UUID,
    payload: ProductVariantUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.update_variant(
            db=db,
            product_id=product_id,
            variant_id=variant_id,
            data=payload,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


@router.patch(
    "/{product_id}/variants/{variant_id}/status",
    response_model=ProductVariantResponse,
    dependencies=[
        Depends(
            require_permission(
                "product.update"
            )
        )
    ],
)
def update_variant_status(
    product_id: UUID,
    variant_id: UUID,
    payload: ProductVariantStatusUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.update_variant_status(
            db=db,
            product_id=product_id,
            variant_id=variant_id,
            is_active=payload.is_active,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


# ============================================================
# CLOUDINARY SIGNED UPLOAD
# ============================================================

@router.post(
    "/{product_id}/images/upload-signature",
    response_model=ProductImageUploadSignatureResponse,
    dependencies=[
        Depends(
            require_permission(
                "product.update"
            )
        )
    ],
)
def generate_image_upload_signature(
    product_id: UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """
    Generate signed Cloudinary upload parameters.

    Intended for the production frontend:
        React Drag & Drop
            ↓
        Cloudinary direct upload
            ↓
        Register public_id with backend
    """

    try:
        return (
            service.ProductService
            .generate_image_upload_signature(
                db=db,
                product_id=product_id,
                current_user=current_user,
            )
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


# ============================================================
# DIRECT BACKEND IMAGE UPLOAD
# ============================================================

@router.post(
    "/{product_id}/images/upload",
    response_model=ProductImageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(
                "product.update"
            )
        )
    ],
)
async def upload_product_image(
    product_id: UUID,
    file: UploadFile = File(...),
    is_primary: bool = Query(False),
    sort_order: int = Query(0, ge=0),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """
    Upload product image directly through the backend.

    Swagger will show:
        product_id
        Choose File
        is_primary
        sort_order
    """

    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type is missing.",
        )

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported image format. "
                "Allowed formats: JPEG, PNG, WEBP, GIF."
            ),
        )

    file_bytes = await file.read()

    # Maximum 10 MB per image.
    max_file_size = 10 * 1024 * 1024

    if len(file_bytes) > max_file_size:
        raise HTTPException(
            status_code=413,
            detail="Image size cannot exceed 10 MB.",
        )

    try:
        return service.ProductService.upload_product_image(
            db=db,
            product_id=product_id,
            file_bytes=file_bytes,
            filename=file.filename or "product-image",
            current_user=current_user,
            is_primary=is_primary,
            sort_order=sort_order,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


# ============================================================
# REGISTER CLOUDINARY IMAGE
# ============================================================

@router.post(
    "/{product_id}/images",
    response_model=ProductImageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(
                "product.update"
            )
        )
    ],
)
def add_product_image(
    product_id: UUID,
    payload: ProductImageCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    """
    Register an image that was already uploaded to Cloudinary.
    """

    try:
        return service.ProductService.add_product_image(
            db=db,
            product_id=product_id,
            data=payload,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


# ============================================================
# LIST PRODUCT IMAGES
# ============================================================

@router.get(
    "/{product_id}/images",
    response_model=list[ProductImageResponse],
    dependencies=[
        Depends(
            require_permission(
                "product.view"
            )
        )
    ],
)
def list_product_images(
    product_id: UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.list_product_images(
            db=db,
            product_id=product_id,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# ============================================================
# UPDATE PRODUCT IMAGE
# ============================================================

@router.patch(
    "/{product_id}/images/{image_id}",
    response_model=ProductImageResponse,
    dependencies=[
        Depends(
            require_permission(
                "product.update"
            )
        )
    ],
)
def update_product_image(
    product_id: UUID,
    image_id: UUID,
    payload: ProductImageUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.ProductService.update_product_image(
            db=db,
            product_id=product_id,
            image_id=image_id,
            data=payload,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)


# ============================================================
# DELETE PRODUCT IMAGE
# ============================================================

@router.delete(
    "/{product_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(
            require_permission(
                "product.update"
            )
        )
    ],
)
def delete_product_image(
    product_id: UUID,
    image_id: UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
):
    try:
        service.ProductService.delete_product_image(
            db=db,
            product_id=product_id,
            image_id=image_id,
            current_user=current_user,
        )

    except service.ProductServiceError as exc:
        raise _service_error(exc)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )