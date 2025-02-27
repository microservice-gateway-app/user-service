from __future__ import annotations

from pydantic import BaseModel, Field

from ..shared.id import RoleId
from .domain import Permission, Role


class RoleInput(BaseModel):
    name: str = Field(description="The name of the role.")
    permissions: set[str] = Field(
        default_factory=set, description="The permissions of the role."
    )


class RolePermissionAssignmentInput(BaseModel):
    role_id: RoleId
    permission: Permission


class RoleView(Role):
    @classmethod
    def from_role(cls, role: Role) -> RoleView:
        return cls(id=role.id, name=role.name, permissions=role.permissions)


class RoleList(BaseModel):
    total: int
    roles: list[RoleView]

    @staticmethod
    def from_roles(roles: list[Role]) -> RoleList:
        role_views = [RoleView.from_role(role) for role in roles]
        return RoleList(total=len(role_views), roles=role_views)
