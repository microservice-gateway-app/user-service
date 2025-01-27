from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID
from datetime import datetime


class MessageResponse(BaseModel):
    message: str


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scope_name: str
    description: str | None = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    permissions: list[PermissionResponse] = []


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: str
    middle_name: str | None = None
    last_name: str
    created_at: datetime
    roles: list[RoleResponse] = []
    prohibited_permissions: set[str] = set()
