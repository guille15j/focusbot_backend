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
    birth_date: Optional[date] = None
    timezone: str = Field("UTC", max_length=50)
    profile_img: Optional[str] = None
    # Detalles de condición médica
    name_detail: Optional[str] = Field(None, max_length=50)
    description_detail: Optional[str] = Field(None, max_length=250)
    severity: SeverityEnum = SeverityEnum.LEVE

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    user_id: int
    created_at: datetime
    verified: bool
    google_id: Optional[str] = None

class UserUpdate(BaseSchema):
    """
    Schema para la actualización parcial del perfil (PATCH).
    Todos los campos son opcionales.
    """
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    nickname: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    birth_date: Optional[date] = None
    timezone: Optional[str] = Field(None, max_length=50)
    profile_img: Optional[str] = None
    
    # Estos campos son los que faltaban y causaban que no se guardaran los detalles
    name_detail: Optional[str] = Field(None, max_length=50)
    description_detail: Optional[str] = Field(None, max_length=250)
    severity: Optional[SeverityEnum] = None