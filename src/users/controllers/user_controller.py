from users.core.domain.permission import PermissionId
from users.core.domain.role import RoleId
from users.core.domain.user import UserId

from ..core.services.user_services import UserServices
from .base import BaseController, controller
from .schemas import MessageResponse, UserResponse


@controller
class UserController(BaseController):
    def __init__(self, service: UserServices) -> None:
        super().__init__(prefix="/users")
        self.service = service

    def init_routes(self) -> None:
        """Define API routes for user management."""
        self.router.get("/{user_id}", response_model=UserResponse)(self.get_user_by_id)
        self.router.post("/{user_id}/roles/{role_id}", response_model=MessageResponse)(
            self.assign_role_to_user
        )
        self.router.delete(
            "/{user_id}/roles/{role_id}", response_model=MessageResponse
        )(self.revoke_role_from_user)
        self.router.post(
            "/{user_id}/permissions/prohibited/{permission_id}",
            response_model=MessageResponse,
        )(self.add_prohibited_permission_to_user)
        self.router.delete(
            "/{user_id}/permissions/prohibited/{permission_id}",
            response_model=MessageResponse,
        )(self.remove_prohibited_permission_from_user)
        self.router.post(
            "/roles/{role_id}/permissions/{permission_id}",
            response_model=MessageResponse,
        )(self.assign_permission_to_role)
        self.router.delete(
            "/roles/{role_id}/permissions/{permission_id}",
            response_model=MessageResponse,
        )(self.revoke_permission_from_role)

    async def get_user_by_id(self, user_id: str) -> UserResponse:
        """Get a user by ID."""
        user = await self.service.get_user_by_id(UserId(value=user_id))
        return UserResponse.model_validate(user)

    async def assign_role_to_user(self, user_id: str, role_id: str) -> MessageResponse:
        """Assign a role to a user."""
        await self.service.assign_role_to_user(
            user_id=UserId(value=user_id), role_id=RoleId(value=role_id)
        )
        return MessageResponse(message="Role assigned successfully")

    async def revoke_role_from_user(
        self, user_id: str, role_id: str
    ) -> MessageResponse:
        """Revoke a role from a user."""
        await self.service.revoke_role_from_user(
            user_id=UserId(value=user_id), role_id=RoleId(value=role_id)
        )
        return MessageResponse(message="Role revoked successfully")

    async def add_prohibited_permission_to_user(
        self,
        user_id: str,
        permission_id: str,
    ) -> MessageResponse:
        """Prohibit a permission for a user."""
        await self.service.add_prohibited_permission_to_user(
            user_id=UserId(value=user_id),
            permission_id=PermissionId(value=permission_id),
        )
        return MessageResponse(message="Permission prohibited successfully")

    async def remove_prohibited_permission_from_user(
        self,
        user_id: str,
        permission_id: str,
    ) -> MessageResponse:
        """Remove the prohibition of a permission from a user."""
        await self.service.remove_prohibited_permission_from_user(
            user_id=UserId(value=user_id),
            permission_id=PermissionId(value=permission_id),
        )
        return MessageResponse(message="Prohibited permission removed successfully")

    async def assign_permission_to_role(
        self,
        role_id: str,
        permission_id: str,
    ) -> MessageResponse:
        """Assign a permission to a role."""
        await self.service.assign_permission_to_role(
            role_id=RoleId(value=role_id),
            permission_id=PermissionId(value=permission_id),
        )
        return MessageResponse(message="Permission assigned to role successfully")

    async def revoke_permission_from_role(
        self,
        role_id: str,
        permission_id: str,
    ) -> MessageResponse:
        """Revoke a permission from a role."""
        await self.service.revoke_permission_from_role(
            role_id=RoleId(value=role_id),
            permission_id=PermissionId(value=permission_id),
        )
        return MessageResponse(message="Permission revoked from role successfully")
