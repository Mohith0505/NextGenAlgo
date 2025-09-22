from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_user_service
from app.models.user import User
from app.schemas.auth import Message
from app.schemas.user import UserRead, UserUpdate
from app.services.users import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User | None = Depends(get_current_user)) -> UserRead:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active user session")
    return UserRead.model_validate(current_user)


@router.get("", response_model=list[UserRead])
def list_users(user_service: UserService = Depends(get_user_service)) -> list[UserRead]:
    return user_service.list_users()


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, payload: UserUpdate, user_service: UserService = Depends(get_user_service)) -> UserRead:
    updated = user_service.update_user(user_id, payload)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated


@router.delete("/{user_id}", response_model=Message)
def delete_user(user_id: UUID, user_service: UserService = Depends(get_user_service)) -> Message:
    deleted = user_service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Message(detail="User removed")
