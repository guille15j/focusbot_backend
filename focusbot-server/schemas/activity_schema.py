from pydantic import Field
from typing import Optional
from datetime import datetime
from schemas.base import BaseSchema
from services.db_service import ActivityState, ActivityCategory, ActivityResults

# --- ACTIVITY TYPES ---
class ActivityTypeBase(BaseSchema):
    name_type: str = Field(..., max_length=50)
    work_duration: int = Field(..., ge=0)
    short_break: int = Field(0, ge=0)
    long_break: int = Field(0, ge=0)
    cycles_before_long: int = Field(0, ge=0)

class ActivityTypeResponse(ActivityTypeBase):
    type_id: int
    user_id: int

# --- ACTIVITIES ---
class ActivityBase(BaseSchema):
    title: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=250)
    category: ActivityCategory = ActivityCategory.OTRAS
    init_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metadata: Optional[dict] = None

class ActivityCreate(ActivityBase):
    type_id: int
    bot_id: int

class ActivityUpdate(BaseSchema):
    type_id: Optional[int] = None
    bot_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    state: Optional[ActivityState] = None
    category: Optional[ActivityCategory] = None
    result: Optional[ActivityResults] = None
    init_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metadata: Optional[dict] = None

class ActivityResponse(ActivityBase):
    activity_id: int
    user_id: int
    type_id: int
    bot_id: int
    state: ActivityState
    result: Optional[ActivityResults]
<<<<<<< HEAD

class ActivityTypeUpdate(BaseSchema):
    name_type: Optional[str] = Field(None, max_length=50)
    work_duration: Optional[int] = Field(None, ge=0)
    short_break: Optional[int] = Field(None, ge=0)
    long_break: Optional[int] = Field(None, ge=0)
    cycles_before_long: Optional[int] = Field(None, ge=0)
=======
    metadata: Optional[dict] = None
>>>>>>> 04cb8f904ed6f2859472f798ef60891ba661fee7
