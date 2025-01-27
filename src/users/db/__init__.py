from injector import Module, provider
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import UserServiceConfigurations
from ..core.services.token_repository import TokenRepository
from ..core.services.user_repository import UserRepository
from ..db.token_repository import TokenRepositoryOnSQLA
from ..db.user_repository import UserRepositoryOnSQLA


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
