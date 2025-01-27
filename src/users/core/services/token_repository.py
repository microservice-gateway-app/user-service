from typing import Protocol

from users.core.domain.user import UserId

from ..domain.token import RefreshToken


class TokenRepository(Protocol):
    async def find_by_token(self, refresh_token: str) -> RefreshToken | None: ...
    async def save_refresh_token(self, refresh_token: RefreshToken) -> None: ...
    async def remove_refresh_token(
        self, user_id: UserId, refresh_token: str
    ) -> None: ...
