from fastapi import APIRouter, HTTPException, status
from typing import List
from app.schemas.user_schema import UserCreate, UserResponse
from app.services import user_service
import asyncpg

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
async def list_users():
    return await user_service.fetch_users()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    try:
        return await user_service.create_user(user)
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user