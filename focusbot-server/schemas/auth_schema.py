from pydantic import Field
from schemas.base import BaseSchema

class LoginSchema(BaseSchema):
    identifier: str = Field(..., description="Email o Nickname")
    password: str = Field(...)

class ResetPasswordSchema(BaseSchema):
    identifier: str = Field(...)
    password: str = Field(..., min_length=8)