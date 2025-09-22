from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.utils.dt import utcnow

from app.api.dependencies import get_user_service
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, Message, Token
from app.schemas.user import UserCreate, UserRead
from app.services.users import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(new_user: UserCreate, user_service: UserService = Depends(get_user_service)) -> UserRead:
    """Create a user using the persistent database layer."""
    try:
        return user_service.create_user(new_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=Token)
def login(login_request: LoginRequest, user_service: UserService = Depends(get_user_service)) -> Token:
    user = user_service.authenticate(login_request.email, login_request.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    expires_delta = timedelta(minutes=30)
    token = create_access_token(subject=str(user.id), expires_delta=expires_delta)
    return Token(access_token=token, expires_at=utcnow() + expires_delta)


@router.get("/health", response_model=Message)
def auth_health() -> Message:
    return Message(detail="Auth service responsive")
