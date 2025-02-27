from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, Security
from pydantic import BaseModel

from users.api.middlewares.access_scopes import has_any_scope
from users.core.access import Actor, UserScope
from users.core.tokens import TokenPairInput, TokenServices

from .base import BaseController, controller


class TokenPairResponse(BaseModel):
    refresh_token: str
    access_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    expiration: datetime


@controller
class TokenController(BaseController):
    def __init__(self, service: TokenServices) -> None:
        super().__init__(prefix="/tokens")
        self.service = service

    def init_routes(self) -> None:
        """Define all the routes related to token generation and validation."""
        self.router.post("", response_model=TokenPairResponse)(self.create_token_pair)
        self.router.post("/refresh", response_model=AccessTokenResponse)(
            self.refresh_access_token
        )
        self.router.delete("")(self.revoke_refresh_token)

    async def create_token_pair(
        self, token_pair_input: TokenPairInput
    ) -> TokenPairResponse:
        """Create and return a pair of access and refresh tokens."""
        try:
            refresh_token, access_token = await self.service.create_token_pair(
                token_pair_input=token_pair_input, valid_from=datetime.now(UTC)
            )
            return TokenPairResponse(
                refresh_token=refresh_token.token, access_token=access_token.token
            )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error creating token pair: {str(e)}"
            )

    async def refresh_access_token(self, refresh_token: str) -> AccessTokenResponse:
        """Generate a new access token from a refresh token."""
        try:
            token = await self.service.get_refresh_token(refresh_token)
            user = await self.service.get_user_from_refresh_token(refresh_token)
            access_token = self.service.create_access_token(
                user=user,
                refresh_token=token,
                valid_from=datetime.now(),
            )
            return AccessTokenResponse(
                access_token=access_token.token, expiration=access_token.expiration
            )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error refreshing access token: {str(e)}"
            )

    async def revoke_refresh_token(
        self,
        refresh_token: str,
        _: Actor = Security(
            has_any_scope,
            scopes=[UserScope.USER_WRITE.value],
        ),
    ) -> None:
        """Revoke a refresh token."""
        try:
            # Revoke the refresh token by removing it from the repository or marking it as invalid
            await self.service.revoke_refresh_token(refresh_token)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error revoking refresh token: {str(e)}"
            )
