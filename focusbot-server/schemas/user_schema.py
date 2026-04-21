from pydantic import Field, EmailStr
from typing import Optional
from datetime import datetime, date
from schemas.base import BaseSchema
from services.db_service import SeverityEnum

class UserBase(BaseSchema):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    nickname: str = Field(..., max_length=20)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    birth_date: date
    timezone: str = Field("UTC", max_length=50)
    name_detail: Optional[str] = Field(None, max_length=50)
    description_detail: Optional[str] = Field(None, max_length=250)
    severity: SeverityEnum = SeverityEnum.LEVE

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    user_id: int
    created_at: datetime