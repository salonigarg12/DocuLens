import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserSignup(BaseModel):
    username: str = Field(
        min_length=6,
        max_length=30,
    )

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    phone_no: str | None = Field(
        default=None,
        max_length=20,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip().lower()

        if not re.fullmatch(r"[a-zA-Z0-9_]+", value):
            raise ValueError(
                "Username can contain only letters, numbers and underscores."
            )

        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty.")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r"[a-z]", value):
            raise ValueError(
                "Password must contain at least one lowercase letter."
            )

        if not re.search(r"\d", value):
            raise ValueError(
                "Password must contain at least one number."
            )

        if not re.search(r"[^a-zA-Z0-9]", value):
            raise ValueError(
                "Password must contain at least one special character."
            )

        return value


class UserResponse(BaseModel):
    username: str
    name: str
    email: EmailStr
    phone_no: str | None

    model_config = {
        "from_attributes": True
    }

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse