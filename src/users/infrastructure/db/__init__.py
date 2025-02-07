from injector import Module, provider
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from users.config import UserServiceConfigurations
from users.core.tokens import TokenRepository
from users.core.users import UserRepository

from .token_repository import TokenRepositoryOnSQLA
from .user_repository import UserRepositoryOnSQLA


class DatabaseModule(Module):
    @provider
    def provide_session(self, config: UserServiceConfigurations) -> AsyncSession:
        engine = create_async_engine(config.DB_URI)
        return async_sessionmaker(engine, class_=AsyncSession)()

    @provider
    def provide_user_repository(self, session: AsyncSession) -> UserRepository:
        return UserRepositoryOnSQLA(session=session)

    @provider
    def provide_token_repository(self, session: AsyncSession) -> TokenRepository:
        return TokenRepositoryOnSQLA(session=session)
