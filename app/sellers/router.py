from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_database
from app.permissions.dependencies import require_permission
from app.sellers.schemas import (
    SellerCreate,
    SellerResponse,
    SellerStatusUpdate,
    SellerUpdate,
)
from app.sellers.service import (
    SellerServiceError,
    create_seller,
    get_seller,
    list_sellers,
    update_seller,
    update_seller_status,
)
from app.users.models import User


router = APIRouter(
    prefix="/sellers",
    tags=["Sellers"],
)


@router.post(
    "",
    response_model=SellerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_seller_endpoint(
    data: SellerCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(
        require_permission("seller.create")
    ),
):
    try:
        return create_seller(
            db=db,
            data=data,
            current_user=current_user,
        )

    except SellerServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[SellerResponse],
)
def list_sellers_endpoint(
    db: Session = Depends(get_database),
    current_user: User = Depends(
        require_permission("seller.view")
    ),
):
    try:
        return list_sellers(
            db=db,
            current_user=current_user,
        )

    except SellerServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get(
    "/{seller_id}",
    response_model=SellerResponse,
)
def get_seller_endpoint(
    seller_id: UUID,
    db: Session = Depends(get_database),
    current_user: User = Depends(
        require_permission("seller.view")
    ),
):
    try:
        return get_seller(
            db=db,
            seller_id=seller_id,
            current_user=current_user,
        )

    except SellerServiceError as exc:
        if str(exc) == "Seller not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{seller_id}",
    response_model=SellerResponse,
)
def update_seller_endpoint(
    seller_id: UUID,
    data: SellerUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(
        require_permission("seller.update")
    ),
):
    try:
        return update_seller(
            db=db,
            seller_id=seller_id,
            data=data,
            current_user=current_user,
        )

    except SellerServiceError as exc:
        if str(exc) == "Seller not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{seller_id}/status",
    response_model=SellerResponse,
)
def update_seller_status_endpoint(
    seller_id: UUID,
    data: SellerStatusUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(
        require_permission("seller.update")
    ),
):
    try:
        return update_seller_status(
            db=db,
            seller_id=seller_id,
            data=data,
            current_user=current_user,
        )

    except SellerServiceError as exc:
        if str(exc) == "Seller not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc