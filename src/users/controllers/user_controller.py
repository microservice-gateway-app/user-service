from typing import Annotated

from fastapi import Body, HTTPException, Security

from ..core.domain.permission import PermissionId
from ..core.domain.role import RoleId
from ..core.domain.user import UserId
from ..core.services.access import Actor, UserScope
from ..core.services.user_services import UserInput, UserList, UserQuery, UserServices
from ..middlewares.access_scopes import has_any_scope
from .base import BaseController, controller
from .schemas import MessageResponse, UserResponse


@controller
class UserController(BaseController):
    def __init__(self, service: UserServices) -> None:
        super().__init__(prefix="/users")
        self.service = service

    def init_routes(self) -> None:
        """Define API routes for user management."""
        self.router.post(
            "", response_model=UserResponse, response_model_exclude_none=True
        )(self.create_user)
        self.router.post(
            "/register", response_model=UserResponse, response_model_exclude_none=True
        )(self.register_user)
        self.router.post("/query", response_model=UserList)(self.query_users)
        self.router.get(
            "/{user_id}", response_model=UserResponse, response_model_exclude_none=True
        )(self.get_user_by_id)
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

    async def get_user_by_id(
        self,
        user_id: str,
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_READ.value, UserScope.USER_READ_SELF.value],
        ),
    ) -> UserResponse:
        """Get a user by ID. Required scope: users."""
        user = await self.service.get_user_by_id(UserId(value=user_id))
        return UserResponse.from_user(user)

    async def query_users(
        self,
        query: Annotated[UserQuery, Body()],
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_READ.value],
        ),
    ) -> UserList:
        """Get a list of users. Required scope: users."""
        return await self.service.query_users(query=query)

    async def create_user(
        self,
        user: Annotated[UserInput, Body()],
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> UserResponse:
        """Create a new user. Required scope: users.write."""
        try:
            created = await self.service.create_user(user_input=user)
            return UserResponse.from_user(created)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def register_user(
        self,
        user: Annotated[UserInput, Body()],
    ) -> UserResponse:
        """Register a new user"""
        try:
            created = await self.service.create_user(user_input=user)
            return UserResponse.from_user(created, exclude_role_and_permissions=True)
        except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

    async def assign_role_to_user(
        self,
        user_id: str,
        role_id: str,
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> MessageResponse:
        """Assign a role to a user. Required scope: users.edit."""
        await self.service.assign_role_to_user(
            user_id=UserId(value=user_id), role_id=RoleId(value=role_id)
        )
        return MessageResponse(message="Role assigned successfully")

    async def revoke_role_from_user(
        self,
        user_id: str,
        role_id: str,
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> MessageResponse:
        """Revoke a role from a user. Required scope: users.edit."""
        await self.service.revoke_role_from_user(
            user_id=UserId(value=user_id), role_id=RoleId(value=role_id)
        )
        return MessageResponse(message="Role revoked successfully")

    async def add_prohibited_permission_to_user(
        self,
        user_id: str,
        permission_id: str,
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> MessageResponse:
        """Prohibit a permission for a user. Required scope: users.edit."""
        await self.service.add_prohibited_permission_to_user(
            user_id=UserId(value=user_id),
            permission_id=PermissionId(value=permission_id),
        )
        return MessageResponse(message="Permission prohibited successfully")

    async def remove_prohibited_permission_from_user(
        self,
        user_id: str,
        permission_id: str,
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> MessageResponse:
        """Remove the prohibition of a permission from a user. Required scope: users.edit."""
        await self.service.remove_prohibited_permission_from_user(
            user_id=UserId(value=user_id),
            permission_id=PermissionId(value=permission_id),
        )
        return MessageResponse(message="Prohibited permission removed successfully")

    async def assign_permission_to_role(
        self,
        role_id: str,
        permission_id: str,
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> MessageResponse:
        """Assign a permission to a role. Required scope: users.edit."""
        await self.service.assign_permission_to_role(
            role_id=RoleId(value=role_id),
            permission_id=PermissionId(value=permission_id),
        )
        return MessageResponse(message="Permission assigned to role successfully")

    async def revoke_permission_from_role(
        self,
        role_id: str,
        permission_id: str,
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> MessageResponse:
        """Revoke a permission from a role. Required scope: users.edit."""
        await self.service.revoke_permission_from_role(
            role_id=RoleId(value=role_id),
            permission_id=PermissionId(value=permission_id),
        )
        return MessageResponse(message="Permission revoked from role successfully")
