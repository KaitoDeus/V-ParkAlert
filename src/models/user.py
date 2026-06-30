# src/models/user.py
import datetime
from sqlalchemy import Column, Integer, String, DateTime, NVARCHAR
from src.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # "citizen", "authority", "ai_system"
    full_name = Column(NVARCHAR(100), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
