from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from jose import JWTError
from pydantic import BaseModel

from ..core.domain.user import User
from ..core.services.token_services import TokenPairInput, TokenServices
from .base import BaseController, controller


class TokenPairResponse(BaseModel):
    refresh_token: str
    access_token: str


class MeResponse(BaseModel):
    user_id: str
    first_name: str
    last_name: str

    @staticmethod
    def from_user(user: User) -> MeResponse:
        return MeResponse(
            user_id=user.id.value, first_name=user.first_name, last_name=user.last_name
        )


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
        self.router.post("/me", response_model=MeResponse)(self.get_me)
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
                token_pair_input=token_pair_input
            )
            return TokenPairResponse(
                refresh_token=refresh_token.token, access_token=access_token.token
            )
        except Exception as e:
            import traceback

            traceback.print_exception(e)
            raise HTTPException(
                status_code=400, detail=f"Error creating token pair: {str(e)}"
            )

    async def get_me(self, access_token: str) -> MeResponse:
        """Retrieve user details from access token."""
        try:
            user = await self.service.get_user_from_access_token(access_token)
            return MeResponse.from_user(user)
        except JWTError:
            raise HTTPException(
                status_code=401, detail="Invalid or expired access token"
            )
        except ValueError:
            raise HTTPException(status_code=404, detail="User not found")

    async def refresh_access_token(self, refresh_token: str) -> AccessTokenResponse:
        """Generate a new access token from a refresh token."""
        try:
            token = await self.service.get_refresh_token(refresh_token)
            access_token = self.service.create_access_token(
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

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        """Revoke a refresh token."""
        try:
            # Revoke the refresh token by removing it from the repository or marking it as invalid
            await self.service.revoke_refresh_token(refresh_token)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error revoking refresh token: {str(e)}"
            )
