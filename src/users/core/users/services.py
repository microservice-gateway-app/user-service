from __future__ import annotations

from ..shared import RoleId, UserId
from .repository import UserRepository
from .schemas import (
    UserAdminCreate,
    UserList,
    UserPasswordChange,
    UserProfileUpdate,
    UserProfileView,
    UserQuery,
    UserRegister,
)


class UserServices:
    """Manage user and profile data."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register_user(self, input: UserRegister) -> None:
        """Register a new user and profile, assign default role."""
        # Create a user object
        user = input.user()
        profile = input.profile(user.id)

        # add default role
        role = await self.user_repository.find_default_role()
        user.assign_role(role)

        # save user and profile
        await self.user_repository.save_user(user)
        await self.user_repository.save_profile(profile)

    async def create_user(self, input: UserAdminCreate) -> None:
        """Admin user creates a new user and profile, assign roles."""
        # Create a user object
        user = input.user()
        profile = input.profile(user.id)

        # add roles, handle nonexistent role_id
        for role_id in input.role_ids:
            role = await self.user_repository.find_role_by_id(RoleId(value=role_id))
            if role:
                user.assign_role(role)

        # save user and profile
        await self.user_repository.save_user(user)
        await self.user_repository.save_profile(profile)

    async def get_user_profile(self, user_id: UserId) -> UserProfileView:
        """Get a user's profile."""
        profile = await self.user_repository.find_profile_by_id(user_id)
        if not profile:
            raise ValueError(f"NOT FOUND: Profile for user {user_id} not found.")
        return UserProfileView.from_profile(profile)

    async def query_users_for_admin(self, query: UserQuery) -> UserList:
        """Query users for an admin."""
        profiles, total = await self.user_repository.query_users(query)
        return UserList.from_profiles(profiles=profiles, total=total, query=query)

    async def update_user_profile(
        self, user_id: UserId, input: UserProfileUpdate
    ) -> UserProfileView:
        """Update a user's profile."""
        profile = await self.user_repository.find_profile_by_id(user_id)
        if not profile:
            raise ValueError(f"NOT FOUND: Profile for user {user_id} not found.")
        updated_profile = input.apply(profile)
        await self.user_repository.save_profile(updated_profile)
        return UserProfileView.from_profile(updated_profile)

    async def change_password(self, user_id: UserId, input: UserPasswordChange) -> None:
        """Change a user's password."""
        user = await self.user_repository.find_user_by_id(user_id)
        if not user:
            raise ValueError(f"NOT FOUND: User {user_id} not found.")
        if not user.verify_password(input.password):
            raise ValueError("INVALID: Incorrect password.")
        user.set_password(input.new_password)
        await self.user_repository.save_user(user)

    async def assign_roles(self, user_id: UserId, role_ids: list[RoleId]) -> None:
        """Admin assigns roles to a user."""
        user = await self.user_repository.find_user_by_id(user_id)
        if not user:
            raise ValueError(f"NOT FOUND: User {user_id} not found.")
        for role_id in role_ids:
            role = await self.user_repository.find_role_by_id(role_id)
            if role:
                user.assign_role(role)
        await self.user_repository.save_user(user)

    async def remove_roles(self, user_id: UserId, role_ids: list[RoleId]) -> None:
        """Admin removes roles from a user."""
        user = await self.user_repository.find_user_by_id(user_id)
        if not user:
            raise ValueError(f"NOT FOUND: User {user_id} not found.")
        for role_id in role_ids:
            role = await self.user_repository.find_role_by_id(role_id)
            if role:
                user.remove_role(role)
        await self.user_repository.save_user(user)

    async def delete_user(self, user_id: UserId) -> None:
        """Admin deletes a user."""
        user = await self.user_repository.find_user_by_id(user_id)
        if not user:
            raise ValueError(f"NOT FOUND: User {user_id} not found.")
        await self.user_repository.delete_user(user.id)
        await self.user_repository.delete_profile(user.id)
