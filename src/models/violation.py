# src/models/violation.py
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, NVARCHAR
from src.models.base import Base

class ViolationReport(Base):
    __tablename__ = "violation_reports"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_plate = Column(String(20), nullable=False, index=True)
    violation_type = Column(NVARCHAR(100), nullable=False)  # e.g., Đỗ xe đè vỉa hè, Đỗ khu vực biển cấm
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    image_url = Column(String, nullable=True)  # supports long text / base64 image data
    reporter_role = Column(String(20), nullable=False)  # "citizen", "ai_system"
    reporter_name = Column(NVARCHAR(100), nullable=False)  # Citizen name or Camera ID
    status = Column(String(20), default="pending", nullable=False)  # "pending", "verified", "rejected"
    duration_seconds = Column(Integer, default=0, nullable=False)
    violation_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
