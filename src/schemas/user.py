# src/schemas/user.py
from pydantic import BaseModel, Field
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(..., pattern="^(citizen|authority|ai_system)$")
    full_name: str = Field(..., min_length=2, max_length=100)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True
