# src/api/v1/auth.py
from fastapi import APIRouter, Depends, status
from src.schemas import UserCreate, UserLogin, Token, UserResponse
from src.models import User
from src.services.auth_service import AuthService
from src.api.deps import get_auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.register_user(user_in)

@router.post("/login", response_model=Token)
def login(login_in: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.authenticate_user(login_in)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
