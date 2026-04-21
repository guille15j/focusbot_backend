from pydantic import Field
from typing import Optional
from datetime import datetime
from schemas.base import BaseSchema
from services.db_service import ActivityCategory

class HistoryResponse(BaseSchema):
    record_id: int
    user_id: int
    init_date_range: datetime
    end_date_range: datetime
    num_completo: int = 0
    num_pospuesto: int = 0
    num_cancelado: int = 0
    num_pendiente: int = 0
    most_category: Optional[ActivityCategory] = None
    total_activities: int = 0
    total_used_time: Optional[int] = None