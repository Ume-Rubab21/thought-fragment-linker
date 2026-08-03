from pydantic import BaseModel, EmailStr, Field


class DirectPasswordReset(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=6)
