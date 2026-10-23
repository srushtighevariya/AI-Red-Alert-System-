from fastapi import APIRouter , Depends

from app.api.dependencies import get_current_user
from app.schemas.user_schema import UserRegisterRequest, UserResponse
from app.services.auth_service import register_user
from app.schemas.user_schema import (
    LoginResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegisterRequest):
    return await register_user(user_data)

@router.post("/login", response_model=LoginResponse)
async def login(login_data: UserLoginRequest):
    return await login_user(login_data)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user["user_id"],
        "full_name": current_user["full_name"],
        "email": current_user["email"],
        "role": current_user["role"],
    }