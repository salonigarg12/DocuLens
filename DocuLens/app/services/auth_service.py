from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from app.schemas.user import UserLogin, UserSignup
from app.utils.security import (
    create_access_token,
    hash_password,
    verify_password,
)


def register_user(
    db: Session,
    signup_data: UserSignup,
) -> User:
    existing_username = get_user_by_username(
        db,
        signup_data.username,
    )

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken.",
        )

    existing_email = get_user_by_email(
        db,
        str(signup_data.email),
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    new_user = User(
        username=signup_data.username,
        name=signup_data.name,
        email=str(signup_data.email),
        phone_no=signup_data.phone_no,
        password_hash=hash_password(
            signup_data.password
        ),
    )

    return create_user(db, new_user)

def authenticate_user(
    db: Session,
    login_data: UserLogin,
) -> tuple[User, str]:
    user = get_user_by_email(
        db,
        str(login_data.email),
    )

    if not user or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(
        login_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(
        username=user.username
    )

    return user, access_token