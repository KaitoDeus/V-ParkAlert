# src/services/auth_service.py
from abc import ABC, abstractmethod
from fastapi import HTTPException, status
from src.repositories.user_repository import IUserRepository
from src.schemas import UserCreate, UserLogin, Token
from src.models import User
from src.core.security import PasswordHasher, TokenGenerator

class IAuthService(ABC):
    @abstractmethod
    def register_user(self, user_in: UserCreate) -> User:
        pass

    @abstractmethod
    def authenticate_user(self, login_in: UserLogin) -> Token:
        pass

class AuthService(IAuthService):
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def register_user(self, user_in: UserCreate) -> User:
        existing = self.user_repo.get_by_username(user_in.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên tài khoản đã tồn tại trong hệ thống."
            )
        
        hashed_password = PasswordHasher.hash_password(user_in.password)
        new_user = User(
            username=user_in.username,
            hashed_password=hashed_password,
            role=user_in.role,
            full_name=user_in.full_name
        )
        return self.user_repo.create(new_user)

    def authenticate_user(self, login_in: UserLogin) -> Token:
        user = self.user_repo.get_by_username(login_in.username)
        if not user or not PasswordHasher.verify_password(login_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tên tài khoản hoặc mật khẩu không chính xác."
            )
        
        access_token = TokenGenerator.create_access_token(data={"sub": user.username})
        return Token(
            access_token=access_token,
            token_type="bearer",
            role=user.role,
            username=user.username,
            full_name=user.full_name
        )
