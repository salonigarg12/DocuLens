from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.dependencies import get_current_user
from app.models.user import User

from app.database import get_db
from app.schemas.user import (
    TokenResponse,
    UserLogin,
    UserResponse,
    UserSignup,
)
from app.services.auth_service import (
    authenticate_user,
    register_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    signup_data: UserSignup,
    db: Annotated[Session, Depends(get_db)],
):
    return register_user(
        db=db,
        signup_data=signup_data,
    )

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    login_data: UserLogin,
    db: Annotated[Session, Depends(get_db)],
):
    user, access_token = authenticate_user(
        db=db,
        login_data=login_data,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_logged_in_user(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    return current_user