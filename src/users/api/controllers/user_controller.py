from fastapi import Body, Query, Security

from users.core.access import Actor, UserScope
from users.core.shared import RoleId, UserId
from users.core.users import (
    UserAdminCreate,
    UserDetailedProfileView,
    UserList,
    UserPasswordChange,
    UserProfileUpdate,
    UserProfileView,
    UserQuery,
    UserRegister,
    UserServices,
)

from ..middlewares.access_scopes import has_any_scope
from .base import BaseController, controller
from .schemas import OperationResultResponse


@controller
class AdminUserController(BaseController):
    """Operations for admin that require user scopes."""

    def __init__(self, user_services: UserServices) -> None:
        super().__init__(prefix="/users/admin")
        self.user_services = user_services

    def init_routes(self) -> None:
        self.router.post("")(self.create_user)
        self.router.post("/query")(self.query_users)
        self.router.get("/{user_id}")(self.get_user)
        self.router.patch("/{user_id}")(self.update_user)
        self.router.delete("/{user_id}")(self.delete_user)
        self.router.post("/{user_id}/roles")(self.add_roles)
        self.router.delete("/{user_id}/roles")(self.remove_roles)

    async def create_user(
        self,
        input: UserAdminCreate = Body(),
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> OperationResultResponse:
        """Admin creates a new user. Required scopes: users.write"""
        await self.user_services.create_user(input)
        return OperationResultResponse(message="User created.")

    async def query_users(
        self,
        query: UserQuery = Body(...),
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_READ.value],
        ),
    ) -> UserList:
        """Query users. Required scopes: users"""
        return await self.user_services.query_users_for_admin(query)

    async def get_user(
        self,
        user_id: str,
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_READ.value],
        ),
    ) -> UserProfileView:
        """Get one user. Required scopes: users"""
        return await self.user_services.get_user_profile(user_id=UserId(value=user_id))

    async def update_user(
        self,
        user_id: str,
        input: UserProfileUpdate = Body(...),
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> UserProfileView:
        """Update a user. Required scopes: users.write"""
        return await self.user_services.update_user_profile(
            user_id=UserId(value=user_id), input=input
        )

    async def delete_user(
        self,
        user_id: str,
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> OperationResultResponse:
        """Delete a user. Required scopes: users.write"""
        await self.user_services.delete_user(UserId(value=user_id))
        return OperationResultResponse(message="User deleted.")

    async def add_roles(
        self,
        user_id: str,
        role_ids: list[str] = Query(...),
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> OperationResultResponse:
        """Add roles to a user. Required scopes: users.write"""
        await self.user_services.assign_roles(
            user_id=UserId(value=user_id),
            role_ids=[RoleId(value=id) for id in role_ids],
        )
        return OperationResultResponse(message="Roles assigned.")

    async def remove_roles(
        self,
        user_id: str,
        role_ids: list[str] = Query(...),
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> OperationResultResponse:
        """Remove roles from a user. Required scopes: users.write"""
        await self.user_services.remove_roles(
            user_id=UserId(value=user_id),
            role_ids=[RoleId(value=id) for id in role_ids],
        )
        return OperationResultResponse(message="Roles removed.")


@controller
class UserController(BaseController):
    """Operations that are public or only require user:self scopes."""

    def __init__(self, user_services: UserServices) -> None:
        super().__init__(prefix="/users")
        self.user_services = user_services

    def init_routes(self) -> None:
        self.router.post("")(self.register_user)
        self.router.get("/me")(self.get_my_profile)
        self.router.patch("/me")(self.update_my_profile)
        self.router.patch("/me/password")(self.change_password)
        self.router.delete("/me")(self.delete_my_profile)

    async def register_user(self, input: UserRegister) -> OperationResultResponse:
        """Register a new user."""
        await self.user_services.register_user(input)
        return OperationResultResponse(message="User registered.")

    async def get_my_profile(
        self,
        actor: Actor = Security(has_any_scope, scopes=[UserScope.USER_READ_SELF.value]),
    ) -> UserProfileView | UserDetailedProfileView:
        """Get my profile. Required scopes: users:self"""
        return await self.user_services.get_user_profile(actor.user_id, detailed=True)

    async def update_my_profile(
        self,
        input: UserProfileUpdate,
        actor: Actor = Security(
            has_any_scope, scopes=[UserScope.USER_WRITE_SELF.value]
        ),
    ) -> UserProfileView:
        """Update my profile. Required scopes: users:self.write"""
        return await self.user_services.update_user_profile(actor.user_id, input)

    async def change_password(
        self,
        input: UserPasswordChange,
        actor: Actor = Security(
            has_any_scope, scopes=[UserScope.USER_WRITE_SELF.value]
        ),
    ) -> OperationResultResponse:
        """Change my password. Required scopes: users:self.write"""
        await self.user_services.change_password(actor.user_id, input)
        return OperationResultResponse(message="Password changed.")

    async def delete_my_profile(
        self,
        actor: Actor = Security(
            has_any_scope, scopes=[UserScope.USER_WRITE_SELF.value]
        ),
    ) -> OperationResultResponse:
        """Delete my profile. Required scopes: users:self.write"""
        await self.user_services.delete_user(actor.user_id)
        return OperationResultResponse(message="User deleted.")
