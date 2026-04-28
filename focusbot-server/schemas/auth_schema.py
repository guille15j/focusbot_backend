from pydantic import Field
from schemas.base import BaseSchema

class LoginSchema(BaseSchema):
    identifier: str = Field(..., description="Email o Nickname")
    password: str = Field(...)

class ResetPasswordSchema(BaseSchema):
    identifier: str = Field(...)
    password: str = Field(..., min_length=8)

class VerifyEmailSchema(BaseSchema):
    """
    Schema para validar la petición de verificación de email.
    
    - email: email del usuario a verificar.
    - codigo: cadena de exactamente 6 caracteres (el código numérico enviado por correo).
    """
    email: str = Field(..., description="Email del usuario a verificar")
    codigo: str = Field(..., min_length=6, max_length=6, description="Código de 6 dígitos recibido por correo")