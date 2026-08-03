import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel): email: EmailStr; password: str = Field(min_length=6)
class UserLogin(BaseModel): email: EmailStr; password: str
class GoogleLoginRequest(BaseModel): id_token: str
class ForgotPasswordRequest(BaseModel): email: EmailStr
class ResetPasswordRequest(BaseModel): token: str; new_password: str = Field(min_length=6)
class MessageResponse(BaseModel): message: str
class UserResponse(BaseModel):
    id: uuid.UUID; email: EmailStr; created_at: datetime
    class Config: from_attributes = True
class Token(BaseModel): access_token: str; token_type: str = 'bearer'
