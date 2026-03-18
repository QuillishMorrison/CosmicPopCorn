from pydantic import BaseModel, EmailStr, Field

from app.models import AdminRoleKey
from app.schemas.common import BaseSchema


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-zА-Яа-яЁё0-9_-]+$")
    password: str = Field(min_length=8, max_length=128)
    station_name: str = Field(min_length=3, max_length=60)
    specialization: str = Field(default="freight_hub")


class LoginRequest(BaseModel):
    identity: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseSchema):
    id: str
    email: str
    username: str
    roles: list[AdminRoleKey] = []


class AuthResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
