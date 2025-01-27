import datetime

from pydantic import BaseModel, Field

from .permission import Permission
from .role import Role
from .uuid import UUID


class UserId(UUID, frozen=True): ...


class User(BaseModel):
    id: UserId = Field(default_factory=UserId, description="Generated UserID")
    email: str = Field(description="User email")
    password: str = Field(description="User password", exclude=True)
    first_name: str = Field(description="First name of user")
    middle_name: str | None = Field(default=None, description="Middle name of user")
    last_name: str = Field(description="Last name of user")
    created_at: datetime.datetime = Field(description="Timestamp of user creation")

    roles: list[Role] = Field(
        default_factory=list, description="List of roles assigned to the user"
    )
    prohibited_permissions: list[str] = Field(
        default_factory=list,
        description="Permissions explicitly prohibited for this user",
    )

    def has_permission(self, permission: Permission) -> bool:
        """
        Check if the user has a specific permission.
        The user inherits permissions from their roles unless overridden.
        """
        # Check if the permission is explicitly prohibited
        if permission.scope_name in self.prohibited_permissions:
            return False

        # Check if the user has the permission through any assigned role
        for role in self.roles:
            if permission.scope_name in role.get_permission_names():
                return True

        # If not found, return False
        return False

    def add_role(self, role: Role) -> None:
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role: Role) -> None:
        self.roles.remove(role)

    def add_prohibited_permission(self, permission: Permission) -> None:
        """Prohibit a permission for the user."""
        if permission.scope_name not in self.prohibited_permissions:
            self.prohibited_permissions.append(permission.scope_name)

    def remove_prohibited_permission(self, permission: Permission) -> None:
        """Remove the prohibition of a permission from the user."""
        if permission.scope_name in self.prohibited_permissions:
            self.prohibited_permissions.remove(permission.scope_name)
