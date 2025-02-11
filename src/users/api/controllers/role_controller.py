from fastapi import HTTPException, Security

from users.core.access import Actor, UserScope
from users.core.roles import (
    RoleInput,
    RolePermissionAssignmentInput,
    RoleView,
    RoleServices,
)
from users.core.shared import RoleId

from ..middlewares.access_scopes import has_any_scope
from .base import BaseController, controller
from .schemas import OperationResultResponse


@controller
class RoleController(BaseController):
    def __init__(self, service: RoleServices) -> None:
        super().__init__(prefix="/roles")
        self.service = service

    def init_routes(self) -> None:
        self.router.post("")(self.create_role)
        self.router.get("/{role_id}")(self.get_role)
        self.router.delete("/{role_id}")(self.delete_role)
        self.router.post("/{role_id}/permissions")(self.assign_permission_to_role)
        self.router.delete("/{role_id}/permissions")(self.remove_permission_from_role)

    async def create_role(
        self,
        input: RoleInput,
        _: Actor = Security(has_any_scope, scopes=[UserScope.USER_WRITE.value]),
    ) -> RoleView:
        """Create a new role."""
        try:
            return await self.service.create_role(input=input)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error creating role: {str(e)}"
            )

    async def get_role(
        self,
        role_id: str,
        _: Actor = Security(has_any_scope, scopes=[UserScope.USER_WRITE.value]),
    ) -> RoleView | None:
        """Retrieve a role by ID."""
        return await self.service.get_role(RoleId(value=role_id))

    async def delete_role(
        self,
        role_id: str,
        _: Actor = Security(has_any_scope, scopes=[UserScope.USER_WRITE.value]),
    ) -> OperationResultResponse:
        """Delete a role."""
        success = await self.service.delete_role(RoleId(value=role_id))
        if not success:
            raise HTTPException(status_code=404, detail="Role not found")
        return OperationResultResponse(
            success=success, message="Role deleted successfully"
        )

    async def assign_permission_to_role(
        self,
        input: RolePermissionAssignmentInput,
        _: Actor = Security(has_any_scope, scopes=[UserScope.USER_WRITE.value]),
    ) -> OperationResultResponse:
        """Assign a permission to a role."""
        success = await self.service.assign_permission_to_role(input)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to assign permission")
        return OperationResultResponse(message="Permission updated successfully")

    async def remove_permission_from_role(
        self,
        input: RolePermissionAssignmentInput,
        _: Actor = Security(has_any_scope, scopes=[UserScope.USER_WRITE.value]),
    ) -> OperationResultResponse:
        """Remove a permission from a role."""
        success = await self.service.remove_permission_from_role(input)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove permission")
        return OperationResultResponse(message="Permission updated successfully")
