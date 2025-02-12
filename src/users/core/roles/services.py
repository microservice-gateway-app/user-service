from __future__ import annotations

from ..shared.id import RoleId
from .domain import Permission, Role
from .repository import RoleRepository
from .schemas import RoleInput, RoleList, RolePermissionAssignmentInput, RoleView


class RoleServices:
    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository

    async def create_role(self, input: RoleInput) -> RoleView:
        """Creates a new role with the given permissions."""
        unique_permissions = set[Permission]()
        for perm in input.permissions:
            namespace, name = perm.split(".")
            existing_perm = await self.role_repository.find_permission(
                namespace=namespace, name=name
            )
            if existing_perm:
                unique_permissions.add(existing_perm)
            else:
                permission = Permission(name=name, namespace=namespace)
                await self.role_repository.ensure_permission_exists(permission)
                unique_permissions.add(permission)

        role = Role(id=RoleId(), name=input.name, permissions=unique_permissions)
        await self.role_repository.save(role)
        return RoleView.from_role(role)

    async def get_role(self, role_id: RoleId) -> RoleView | None:
        """Retrieve a role by its ID."""
        role = await self.role_repository.find_by_id(role_id)
        return RoleView.from_role(role) if role else None

    async def list_roles(self) -> RoleList:
        """Lists all roles."""
        roles = await self.role_repository.find_all()
        return RoleList.from_roles(roles)

    async def delete_role(self, role_id: RoleId) -> bool:
        """Deletes a role if it exists, without affecting shared permissions."""
        role = await self.role_repository.find_by_id(role_id)
        if not role:
            return False

        await self.role_repository.delete(role)
        return True

    async def assign_permission_to_role(
        self, input: RolePermissionAssignmentInput
    ) -> bool:
        """Assigns a permission to a role, ensuring it exists first."""
        role_id = input.role_id
        permission = input.permission

        role = await self.role_repository.find_by_id(role_id)
        if not role:
            return False
        permission = await self.role_repository.ensure_permission_exists(permission)
        role.permissions.add(permission)
        await self.role_repository.save(role)
        return True

    async def remove_permission_from_role(
        self, input: RolePermissionAssignmentInput
    ) -> bool:
        """Removes a permission from a role while keeping it if other roles use it."""
        role_id = input.role_id
        permission = input.permission
        role = await self.role_repository.find_by_id(role_id)
        if not role or permission not in role.permissions:
            return False

        role.permissions.remove(permission)
        await self.role_repository.save(role)

        # If no other role is using this permission, it might be safe to delete it (optional logic)
        if not await self.role_repository.any_role_uses_permission(permission):
            await self.role_repository.ensure_permission_deleted(permission)

        return True
