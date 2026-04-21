from pydantic import Field
from typing import Optional
from datetime import datetime
from schemas.base import BaseSchema
from services.db_service import BotStatus
import re

class BotBase(BaseSchema):
    mac_address: str = Field(..., max_length=17)
    custom_name: str = Field("Focus-Bot", max_length=50)

    @classmethod
    def validate_mac(cls, v: str):
        # Validación rigorosa para TFG usando Regex
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        if not re.match(pattern, v):
            raise ValueError('Formato de MAC address inválido')
        return v.upper()

class BotCreate(BotBase):
    pass

class BotResponse(BotBase):
    bot_id: int
    user_id: Optional[int]
    status: BotStatus
    last_sync: Optional[datetime]

class BotCommandSchema(BaseSchema):
    mac: str
    comando: str

class BotUpdate(BaseSchema):
    custom_name: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None