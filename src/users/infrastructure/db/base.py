import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase): ...


class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.logger = logging.getLogger(self.__class__.__qualname__)
