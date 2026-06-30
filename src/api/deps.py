# src/api/deps.py
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models import User
from src.core.config import settings
from src.repositories.user_repository import UserRepository, IUserRepository
from src.repositories.violation_repository import ViolationRepository, IViolationRepository
from src.services.camera_service import CameraService, ICameraService
from src.services.auth_service import AuthService, IAuthService
from src.services.violation_service import ViolationService, IViolationService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

# 1. Base Repositories
def get_user_repository(db: Session = Depends(get_db)) -> IUserRepository:
    return UserRepository(db)

def get_violation_repository(db: Session = Depends(get_db)) -> IViolationRepository:
    return ViolationRepository(db)

# 2. Base Services
def get_camera_service() -> ICameraService:
    return CameraService()

def get_auth_service(user_repo: IUserRepository = Depends(get_user_repository)) -> IAuthService:
    return AuthService(user_repo)

def get_violation_service(
    violation_repo: IViolationRepository = Depends(get_violation_repository),
    camera_service: ICameraService = Depends(get_camera_service)
) -> IViolationService:
    return ViolationService(violation_repo, camera_service)

# 3. Authentication & Authorization dependencies
def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: IUserRepository = Depends(get_user_repository)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = user_repo.get_by_username(username)
    if user is None:
        raise credentials_exception
    return user

def get_current_user_from_token_or_param(
    token_header: str = Depends(oauth2_scheme),
    token_query: str = Query(None, alias="token"),
    user_repo: IUserRepository = Depends(get_user_repository)
) -> User:
    token = token_header or token_query
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = user_repo.get_by_username(username)
    if user is None:
        raise credentials_exception
    return user

def require_role(allowed_roles: list[str]):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tài khoản không có quyền thực hiện hành động này. Yêu cầu: {', '.join(allowed_roles)}"
            )
        return current_user
    return dependency

def require_role_from_token_or_param(allowed_roles: list[str]):
    def dependency(current_user: User = Depends(get_current_user_from_token_or_param)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tài khoản không có quyền thực hiện hành động này. Yêu cầu: {', '.join(allowed_roles)}"
            )
        return current_user
    return dependency
