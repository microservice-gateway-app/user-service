from pydantic import BaseModel, Field

from users.core.domain.uuid import UUID


class PermissionId(UUID, frozen=True): ...


class Permission(BaseModel):
    id: PermissionId = Field(default_factory=PermissionId)
    scope_name: str = Field(
        description="The name of the permission (e.g., 'read', 'write')"
    )
    description: str | None = Field(
        default=None, description="Optional description of the permission"
    )

    def __str__(self) -> str:
        return self.scope_name
