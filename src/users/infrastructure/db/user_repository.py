from __future__ import annotations

from typing import Optional

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from users.core.shared import RoleId, UserId
from users.core.users import UserQuery, UserRepository
from users.core.users.domain import Profile, Role, User

from .base import BaseRepository
from .orm import ProfileORM, RoleORM, UserORM, UserRoleORM


# Repository Implementation
class UserRepositoryOnSQLA(UserRepository, BaseRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_user(self, user: User) -> None:
        user_orm = UserORM(**user.model_dump())
        self.session.add(user_orm)
        await self.session.commit()

    async def save_profile(self, profile: Profile) -> None:
        profile_orm = ProfileORM(**profile.model_dump())
        self.session.add(profile_orm)
        await self.session.commit()

    async def find_user_by_id(self, user_id: UserId) -> Optional[User]:
        result = await self.session.get(UserORM, user_id.value)
        return User.model_validate(result) if result else None

    async def find_profile_by_id(self, user_id: UserId) -> Optional[Profile]:
        result = await self.session.get(ProfileORM, user_id.value)
        return Profile.model_validate(result) if result else None

    async def query_users(self, query: UserQuery) -> tuple[list[Profile], int]:
        stmt = select(ProfileORM)

        if query.email_like:
            stmt = stmt.where(ProfileORM.email.ilike(f"%{query.email_like}%"))
        if query.name_like:
            stmt = stmt.where(
                (ProfileORM.first_name + " " + ProfileORM.last_name).ilike(
                    f"%{query.name_like}%"
                )
            )
        if query.role_ids:
            stmt = (
                stmt.select_from(ProfileORM)
                .join(UserRoleORM, ProfileORM.user_id == UserRoleORM.user_id)
                .where(UserRoleORM.role_id.in_(query.role_ids))
            )

        total_count = await self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        )

        results = await self.session.execute(
            stmt.offset((query.page - 1) * query.page_size).limit(query.page_size)
        )
        profiles = [Profile.model_validate(row) for row in results.scalars().all()]

        return profiles, total_count.scalar_one()

    async def find_default_role(self) -> Role:
        result = await self.session.execute(
            select(RoleORM).where(RoleORM.name == "user")
        )
        return Role.model_validate(result.scalar_one())

    async def find_role_by_id(self, role_id: RoleId) -> Optional[Role]:
        result = await self.session.get(RoleORM, role_id)
        return Role.model_validate(result) if result else None

    async def delete_user(self, user_id: UserId) -> None:
        result = await self.session.get(UserORM, user_id)
        if result:
            await self.session.delete(result)
            await self.session.commit()

    async def delete_profile(self, user_id: UserId) -> None:
        result = await self.session.get(ProfileORM, user_id)
        if result:
            await self.session.delete(result)
            await self.session.commit()
