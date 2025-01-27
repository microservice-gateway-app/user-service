from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import delete, select
from sqlalchemy.exc import SQLAlchemyError

from ..core.domain.token import RefreshToken, RefreshTokenId
from ..core.domain.user import UserId
from ..core.services.token_repository import TokenRepository
from .base import Base


class RefreshTokenRecord(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[str] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(unique=True)
    expiration: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)


class TokenRepositoryOnSQLA(TokenRepository):
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
            user_id=record.id,
        )

    async def save_refresh_token(self, refresh_token: RefreshToken) -> None:
        """Save a refresh token to the database."""
        try:
            # Create a RefreshTokenModel from the domain model RefreshToken
            token_model = RefreshTokenRecord(
                id=refresh_token.id.value,
                token=refresh_token.token,
                expiration=refresh_token.expiration,
                user_id=refresh_token.user_id,
            )

            # Add to the session and commit the transaction
            self.session.add(token_model)
            await self.session.commit()

        except SQLAlchemyError as e:
            await self.session.rollback()  # Rollback on error
            raise Exception(f"Error saving refresh token: {str(e)}")

    async def remove_refresh_token(self, user_id: UserId, refresh_token: str) -> None:
        """Remove a refresh token from the database."""
        try:
            # Construct delete statement
            stmt = (
                delete(RefreshTokenRecord)
                .where(RefreshTokenRecord.user_id == user_id.value)
                .where(RefreshTokenRecord.token == refresh_token)
            )

            # Execute the delete statement
            result = await self.session.execute(stmt)

            # If no rows are deleted, raise an error
            if result.rowcount == 0:
                raise ValueError(f"Refresh token not found for user {user_id.value}.")

            await self.session.commit()  # Commit the transaction

        except SQLAlchemyError as e:
            await self.session.rollback()  # Rollback on error
            raise Exception(f"Error removing refresh token: {str(e)}")
