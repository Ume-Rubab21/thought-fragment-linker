import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True  # lets this read directly from a SQLAlchemy User object


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"