from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRoleEnum(str, Enum):
    owner = "owner"
    admin = "admin"
    trader = "trader"
    viewer = "viewer"


class UserStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    blocked = "blocked"


class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRoleEnum = UserRoleEnum.trader
    status: UserStatusEnum = UserStatusEnum.active
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[UserRoleEnum] = None
    status: Optional[UserStatusEnum] = None
    password: Optional[str] = None
    is_superuser: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)
