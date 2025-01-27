from datetime import UTC, datetime
from typing import Sequence

from pydantic import BaseModel
from bcrypt import hashpw, gensalt, checkpw


from ..domain.permission import Permission, PermissionId
from ..domain.role import Role, RoleId
from ..domain.user import User, UserId
from .user_repository import UserRepository


def hash_password(raw_password: str) -> str:
    salt = gensalt()
    return hashpw(password=raw_password.encode(), salt=salt).decode()


def check_password(raw_password: str, hashed_password: str) -> bool:
    return checkpw(
        password=raw_password.encode(), hashed_password=hashed_password.encode()
    )


class UserInput(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    middle_name: str | None = None

    def to_user(self) -> User:
        return User(
            id=UserId(),
            email=self.email,
            password=hash_password(self.password),
            first_name=self.first_name,
            middle_name=self.middle_name,
            last_name=self.last_name,
            created_at=datetime.now(UTC),
            roles=[],
            prohibited_permissions=[],
        )


class UserServices:
    """Perform CRUD operations on User, Roles & Permissions"""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def create_user(self, user: User) -> User:
        """Create a new user."""
        await self.repository.save(user)
        return user

    async def get_user_by_id(self, user_id: UserId) -> User:
        """Retrieve a user by their ID."""
        user = await self.repository.find_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id.value} not found.")
        return user

    async def update_user(self, user: User) -> User:
        """Update an existing user."""
        await self.repository.save(user)
        return user

    async def delete_user(self, user_id: UserId) -> None:
        """Delete a user by their ID."""
        await self.repository.delete(user_id)

    async def get_user_roles(self, user_id: UserId) -> Sequence[Role]:
        """Get the roles of a user."""
        return await self.repository.get_user_roles(user_id)

    async def get_user_permissions(self, user_id: UserId) -> Sequence[Permission]:
        """Get the permissions of a user."""
        user = await self.get_user_by_id(user_id)
        permissions = list[Permission]()
        for role in user.roles:
            permissions.extend(role.permissions)
        # Return the unique permissions across all roles
        return list({permission.id: permission for permission in permissions}.values())

    async def assign_role_to_user(self, user_id: UserId, role_id: RoleId) -> None:
        """Assign a role to a user by role ID."""
        user = await self.get_user_by_id(user_id)
        role = await self.repository.find_role_by_id(role_id)
        if role not in user.roles:
            user.add_role(role)
            await self.repository.save(user)

    async def revoke_role_from_user(self, user_id: UserId, role_id: RoleId) -> None:
        """Revoke a role from a user by role ID."""
        user = await self.get_user_by_id(user_id)
        role = await self.repository.find_role_by_id(role_id)
        if role in user.roles:
            user.remove_role(role)
            await self.repository.save(user)

    async def add_prohibited_permission_to_user(
        self, user_id: UserId, permission_id: PermissionId
    ) -> None:
        """Prohibit a permission for a user by permission ID."""
        user = await self.get_user_by_id(user_id)
        permission = await self.repository.find_permission_by_id(permission_id)
        user.add_prohibited_permission(permission)
        await self.repository.save(user)

    async def remove_prohibited_permission_from_user(
        self, user_id: UserId, permission_id: PermissionId
    ) -> None:
        """Remove the prohibition of a permission from a user by permission ID."""
        user = await self.get_user_by_id(user_id)
        permission = await self.repository.find_permission_by_id(permission_id)
        user.remove_prohibited_permission(permission)
        await self.repository.save(user)

    async def assign_permission_to_role(
        self, role_id: RoleId, permission_id: PermissionId
    ) -> None:
        """Assign a permission to a role by role and permission IDs."""
        role = await self.repository.find_role_by_id(role_id)
        permission = await self.repository.find_permission_by_id(permission_id)
        if permission not in role.permissions:
            role.permissions.append(permission)
            await self.repository.save_role(role)

    async def revoke_permission_from_role(
        self, role_id: RoleId, permission_id: PermissionId
    ) -> None:
        """Revoke a permission from a role by role and permission IDs."""
        role = await self.repository.find_role_by_id(role_id)
        permission = await self.repository.find_permission_by_id(permission_id)
        if permission in role.permissions:
            role.permissions.remove(permission)
            await self.repository.save_role(role)
