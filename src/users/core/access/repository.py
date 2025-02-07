from typing import Protocol

from ..shared import UserId
from .access_user import AccessUser


class AccessRepository(Protocol):
    async def find_user_by_id(self, id: UserId) -> AccessUser | None: ...
