from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from users.core.domain.user import User, UserId


class MessageResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    # exclude in serialization if None
    model_config = ConfigDict(from_attributes=True)

    id: UserId
    email: EmailStr
    first_name: str
    middle_name: str | None = None
    last_name: str
    created_at: datetime
    roles: list[str] | None = Field(default=None)
    permissions: set[str] | None = Field(default=None)

    @staticmethod
    def from_user(
        user: User, exclude_role_and_permissions: bool = False
    ) -> UserResponse:
        if exclude_role_and_permissions:
            return UserResponse(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                middle_name=user.middle_name,
                last_name=user.last_name,
                created_at=user.created_at,
            )
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            created_at=user.created_at,
            roles=[role.name for role in user.roles],
            permissions={
                permission.scope_name
                for role in user.roles
                for permission in role.permissions
                if permission.scope_name not in user.prohibited_permissions
            },
        )
