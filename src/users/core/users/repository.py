from __future__ import annotations

from typing import Protocol

from ..shared import RoleId, UserId
from .domain.profile import Profile
from .domain.role import Role
from .domain.user import User
from .schemas import UserQuery


class UserRepository(Protocol):
    async def save_user(self, user: User) -> None: ...
    async def save_profile(self, profile: Profile) -> None: ...
    async def find_user_by_id(self, user_id: UserId) -> User | None: ...
    async def find_profile_by_id(self, user_id: UserId) -> Profile | None: ...
    async def query_users(self, query: UserQuery) -> tuple[list[Profile], int]: ...
    async def find_default_role(self) -> Role: ...
    async def find_role_by_id(self, role_id: RoleId) -> Role | None: ...
    async def delete_user(self, user_id: UserId) -> None: ...
    async def delete_profile(self, user_id: UserId) -> None: ...
