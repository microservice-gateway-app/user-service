from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from users.core.shared import RoleId, UserId
from users.core.users import UserQuery, UserRepository
from users.core.users.domain import Profile, Role, User
from users.core.users.domain.permission import Permission
from users.core.users.domain.user import UserRole

from .base import BaseRepository
from .orm import ProfileORM, RoleORM, UserORM, UserRoleORM


def map_user_orm_to_user(user_orm: UserORM) -> User:
    roles = [
        UserRole(
            user_id=UserId(value=user_orm.id),
            role=Role(
                id=RoleId(value=role.id),
                name=role.name,
                permissions=[
                    Permission(name=permission.name, namespace=permission.namespace)
                    for permission in role.permissions
                ],
            ),
        )
        for role in user_orm.roles
    ]
    return User(
        id=UserId(value=user_orm.id),
        email=user_orm.email,
        password_hash=user_orm.password_hash,
        roles=roles,
    )


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

    async def find_user_by_id(self, user_id: UserId) -> User | None:
        stmt = (
            select(UserORM)
            .options(selectinload(UserORM.roles).selectinload(RoleORM.permissions))
            .where(UserORM.id == user_id.value)
        )
        result = await self.session.execute(stmt)
        user_orm = result.scalar_one_or_none()
        if not user_orm:
            return None
        return map_user_orm_to_user(user_orm)

    async def find_profile_by_id(self, user_id: UserId) -> Profile | None:
        result = await self.session.get(ProfileORM, user_id.value)
        return (
            Profile.model_validate(result) if result and not result.deleted_at else None
        )

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

        stmt = stmt.where(ProfileORM.deleted_at.is_not(None))

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

    async def find_role_by_id(self, role_id: RoleId) -> Role | None:
        result = await self.session.get(RoleORM, role_id)
        return Role.model_validate(result) if result else None

    async def delete_user(self, user_id: UserId) -> None:
        result = await self.session.get(UserORM, user_id)
        if result:
            result.soft_delete()
            await self.session.commit()

    async def delete_profile(self, user_id: UserId) -> None:
        result = await self.session.get(ProfileORM, user_id)
        if result:
            result.soft_delete()
            await self.session.commit()
