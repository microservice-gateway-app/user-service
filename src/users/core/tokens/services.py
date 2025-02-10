import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from .domain.token import AccessToken, RefreshToken, RefreshTokenId
from .domain.token_user import TokenUser
from .repository import TokenRepository
from .schemas import TokenConfigurations, TokenPairInput


class TokenServices:
    def __init__(
        self,
        token_repository: TokenRepository,
        config: TokenConfigurations,
    ):
        self.token_repository = token_repository
        self.config = config

    async def create_refresh_token(
        self, user: TokenUser, valid_from: datetime
    ) -> RefreshToken:
        # create token
        refresh_token = RefreshToken(
            token=secrets.token_urlsafe(128),
            expiration=valid_from + timedelta(days=self.config.REFRESH_TOKEN_TTL_DAYS),
            user_id=user.id.value,
        )
        await self.token_repository.save_refresh_token(refresh_token)
        return refresh_token

    def create_access_token(
        self, user: TokenUser, refresh_token: RefreshToken, valid_from: datetime
    ) -> AccessToken:
        # Extract user information from refresh token
        refresh_token_id = refresh_token.id

        # Set expiration time for the access token (shorter-lived)
        expire = valid_from + timedelta(seconds=self.config.ACCESS_TOKEN_TTL_SECONDS)

        # Define JWT payload for access token
        to_encode: dict[str, Any] = {
            "sub": user.id.value,
            "rtk": refresh_token_id.value,  # Subject: refresh token ID
            "exp": expire,  # Expiration time
            # get scopes from user roles & permissions
            "scopes": user.scopes,
        }

        # Encode the access token (sign with secret key)
        access_token = jwt.encode(
            to_encode, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM
        )

        # Return the generated access token wrapped in an AccessToken object
        return AccessToken(token=access_token, expiration=expire)

    async def get_user_from_refresh_token(self, refresh_token: str) -> TokenUser:
        user = await self.token_repository.find_user_by_refresh_token(
            refresh_token=refresh_token
        )
        if not user:
            raise ValueError("Not found user by refresh token")
        return user

    async def get_user_from_access_token(self, access_token: str) -> TokenUser:
        # Decode the JWT access token
        payload = jwt.decode(
            access_token,
            self.config.SECRET_KEY,
            algorithms=[self.config.ALGORITHM],
        )

        # Extract user ID from the decoded token
        refresh_token_id = payload.get("rtk")
        if refresh_token_id is None:
            raise JWTError("Refresh Token ID not found in token")

        # Check token expiration (if expired, raise an exception)
        expiration_time = payload.get("exp")
        if expiration_time is None or datetime.now(UTC) > datetime.fromtimestamp(
            expiration_time, tz=UTC
        ):
            raise JWTError("Access token has expired")

        # Fetch user from repository using the extracted user ID
        user = await self.token_repository.find_user_by_refresh_token_id(
            RefreshTokenId(value=refresh_token_id)
        )
        if not user:
            raise ValueError(f"User not found: id={refresh_token_id}")
        return user

    async def get_refresh_token(self, refresh_token: str) -> RefreshToken:
        token = await self.token_repository.find_by_token(refresh_token)
        if not token:
            raise ValueError("Token not found")
        return token

    async def create_token_pair(
        self, token_pair_input: TokenPairInput, valid_from: datetime
    ) -> tuple[RefreshToken, AccessToken]:
        user = await self.token_repository.find_user_by_email(
            email=token_pair_input.email
        )
        if not user or not user.verify_password(token_pair_input.password):
            raise ValueError("Incorrect username or password.")
        refresh_token = await self.create_refresh_token(
            user=user, valid_from=valid_from
        )
        access_token = self.create_access_token(
            user=user, refresh_token=refresh_token, valid_from=valid_from
        )
        return (refresh_token, access_token)

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        """Revoke the given refresh token."""
        try:
            # Find the refresh token in the repository to ensure it exists
            user = await self.token_repository.find_user_by_refresh_token(refresh_token)

            if not user:
                raise ValueError("Refresh token not found")

            # Remove the refresh token or mark it as invalid
            await self.token_repository.remove_refresh_token(
                user_id=user.id, refresh_token=refresh_token
            )

        except Exception as e:
            raise ValueError(f"Error revoking refresh token: {str(e)}")
