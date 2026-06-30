# src/schemas/violation.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ViolationReportCreate(BaseModel):
    vehicle_plate: str
    violation_type: str
    latitude: float
    longitude: float
    image_url: Optional[str] = None
    duration_seconds: int = 0

class ViolationReportUpdate(BaseModel):
    status: str = Field(..., pattern="^(verified|rejected)$")

class ViolationReportResponse(BaseModel):
    id: int
    vehicle_plate: str
    violation_type: str
    latitude: float
    longitude: float
    image_url: Optional[str] = None
    reporter_role: str
    reporter_name: str
    status: str
    duration_seconds: int
    violation_time: datetime
    created_at: datetime

    class Config:
        from_attributes = True
