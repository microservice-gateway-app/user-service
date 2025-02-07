from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import delete, select

from users.core.shared import UserId
from users.core.tokens import TokenRepository
from users.core.tokens.domain import RefreshToken, RefreshTokenId, TokenUser

from .base import BaseRepository
from .orm import RefreshTokenRecord, RoleORM, UserORM


class TokenRepositoryOnSQLA(TokenRepository, BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_token(self, refresh_token: str) -> RefreshToken | None:
        stmt = select(RefreshTokenRecord).filter_by(token=refresh_token)
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if not record:
            return None
        return RefreshToken(
            id=RefreshTokenId(value=record.id),
            token=record.token,
            expiration=record.expiration,
            user_id=record.user_id,
        )

    def _map_to_token_user(self, record: UserORM) -> TokenUser:
        scopes = {
            permission.full_name
            for role in record.roles
            for permission in role.permissions
        }

        return TokenUser.model_validate(
            {
                "id": str(record.id),
                "email": record.email,
                "password_hash": record.password_hash,
                "scopes": sorted(scopes),
            }
        )

    async def find_user_by_refresh_token_id(
        self, refresh_token_id: RefreshTokenId
    ) -> TokenUser | None:
        stmt = (
            select(UserORM)
            .options(selectinload(UserORM.roles).selectinload(RoleORM.permissions))
            .join(RefreshTokenRecord, RefreshTokenRecord.user_id == UserORM.id)
            .filter(RefreshTokenRecord.id == refresh_token_id.value)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        return self._map_to_token_user(record) if record else None

    async def find_user_by_refresh_token(self, refresh_token: str) -> TokenUser | None:
        stmt = (
            select(UserORM)
            .options(selectinload(UserORM.roles).selectinload(RoleORM.permissions))
            .join(RefreshTokenRecord, RefreshTokenRecord.user_id == UserORM.id)
            .filter(RefreshTokenRecord.token == refresh_token)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        return self._map_to_token_user(record) if record else None

    async def find_user_by_id(self, id: UserId) -> TokenUser | None:
        stmt = (
            select(UserORM)
            .options(selectinload(UserORM.roles).selectinload(RoleORM.permissions))
            .filter_by(id=id.value)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        return self._map_to_token_user(record) if record else None

    async def find_user_by_email(self, email: str) -> TokenUser | None:
        stmt = (
            select(UserORM)
            .options(selectinload(UserORM.roles).selectinload(RoleORM.permissions))
            .filter_by(email=email)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        return self._map_to_token_user(record) if record else None

    async def save_refresh_token(self, refresh_token: RefreshToken) -> None:
        try:
            token_model = RefreshTokenRecord(
                id=refresh_token.id.value,
                token=refresh_token.token,
                expiration=refresh_token.expiration,
                user_id=refresh_token.user_id,
            )
            self.session.add(token_model)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error saving refresh token: {str(e)}")

    async def remove_refresh_token(self, user_id: UserId, refresh_token: str) -> None:
        try:
            stmt = (
                delete(RefreshTokenRecord)
                .where(RefreshTokenRecord.user_id == user_id.value)
                .where(RefreshTokenRecord.token == refresh_token)
            )
            result = await self.session.execute(stmt)
            if result.rowcount == 0:
                raise ValueError(f"Refresh token not found for user {user_id.value}.")
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error removing refresh token: {str(e)}")
