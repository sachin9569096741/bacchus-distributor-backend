from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest, TokenResponse, UserResponse
from app.auth.service import AuthenticationError, login
from app.core.dependencies import get_current_user, get_database
from app.users.models import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    credentials: LoginRequest,
    db: Session = Depends(get_database),
):
    try:
        access_token = login(db, credentials)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )

    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user