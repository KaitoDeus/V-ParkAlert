# src/repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.orm import Session
from src.models import User
from src.repositories.base import BaseRepository

class IUserRepository(ABC):
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        pass

class UserRepository(BaseRepository[User], IUserRepository):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
