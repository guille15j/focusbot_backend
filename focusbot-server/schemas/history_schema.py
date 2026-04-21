from pydantic import Field
from datetime import datetime
from schemas.base import BaseSchema

class HistoryCalculate(BaseSchema):
    init_date_range: datetime
    end_date_range: datetime

class HistoryResponse(BaseSchema):
    record_id: int
    user_id: int
    init_date_range: datetime
    end_date_range: datetime
    num_completo: int = 0
    num_pospuesto: int = 0
    num_cancelado: int = 0
    num_pendiente: int = 0
    total_activities: int = 0
    total_used_time: int = 0