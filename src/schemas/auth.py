# src/schemas/auth.py
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    full_name: str
