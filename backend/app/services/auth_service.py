from fastapi import HTTPException


from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import create_user, find_user_by_email
from app.schemas.user_schema import UserRegisterRequest , UserLoginRequest


async def register_user(user_data: UserRegisterRequest) -> dict:
    existing_user = await find_user_by_email(user_data.email)

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists",
        )

    user_to_save = {
        "full_name": user_data.full_name,
        "email": user_data.email.lower(),
        "hashed_password": hash_password(user_data.password),
        "role": "user",
        "is_active": True,
    }

    user_id = await create_user(user_to_save)

    return {
        "user_id": user_id,
        "full_name": user_to_save["full_name"],
        "email": user_to_save["email"],
        "role": user_to_save["role"],
    }

async def login_user(login_data: UserLoginRequest) -> dict:
    user = await find_user_by_email(login_data.email)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    password_is_valid = verify_password(
        login_data.password,
        user["hashed_password"],
    )

    if not password_is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    user_response = {
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
    }

    access_token = create_access_token(
        data={
            "sub": user["user_id"],
            "email": user["email"],
            "role": user["role"],
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response,
    }