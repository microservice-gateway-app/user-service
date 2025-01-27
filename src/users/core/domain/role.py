from pydantic import BaseModel, Field

from .permission import Permission
from .uuid import UUID


class RoleId(UUID, frozen=True): ...


class Role(BaseModel):
    id: RoleId = Field(default_factory=RoleId)
    name: str = Field()
    permissions: list[Permission] = Field(default_factory=list)

    def get_permission_names(self) -> list[str]:
        """Return the names of all permissions associated with this role."""
        return [permission.scope_name for permission in self.permissions]
