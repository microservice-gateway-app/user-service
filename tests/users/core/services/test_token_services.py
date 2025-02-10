from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from users.core.tokens.domain.token import AccessToken, RefreshToken
from users.core.tokens.domain.token_user import TokenUser
from users.core.tokens.repository import TokenRepository
from users.core.tokens.schemas import TokenConfigurations, TokenPairInput
from users.core.tokens.services import TokenServices


@pytest.fixture
def token_repository() -> AsyncMock:
    return AsyncMock(spec=TokenRepository)


@pytest.fixture
def config() -> TokenConfigurations:
    return TokenConfigurations(
        SECRET_KEY="test_secret",
        ALGORITHM="HS256",
        ACCESS_TOKEN_TTL_SECONDS=3600,
        REFRESH_TOKEN_TTL_DAYS=7,
    )


@pytest.fixture
def token_services(
    token_repository: AsyncMock, config: TokenConfigurations
) -> TokenServices:
    return TokenServices(token_repository, config)


@pytest.fixture
def token_user() -> MagicMock:
    return MagicMock(
        id=MagicMock(value="user_id"),
        scopes=["read", "write"],
        password_hash=MagicMock(),
    )


@pytest.fixture
def refresh_token() -> RefreshToken:
    return RefreshToken(
        token="refresh_token",
        expiration=datetime.now(UTC) + timedelta(days=7),
        user_id="user_id",
    )


@pytest.fixture
def access_token() -> AccessToken:
    return AccessToken(
        token="access_token", expiration=datetime.now(UTC) + timedelta(seconds=3600)
    )


@pytest.mark.asyncio
async def test_create_refresh_token(
    token_services: TokenServices, token_user: TokenUser
) -> None:
    valid_from = datetime.now(UTC)
    refresh_token = await token_services.create_refresh_token(token_user, valid_from)
    assert refresh_token.token is not None
    assert refresh_token.expiration == valid_from + timedelta(days=7)
    assert refresh_token.user_id == token_user.id.value


def test_create_access_token(
    token_services: TokenServices, token_user: TokenUser, refresh_token: RefreshToken
) -> None:
    valid_from = datetime.now(UTC)
    access_token = token_services.create_access_token(
        token_user, refresh_token, valid_from
    )
    assert access_token.token is not None
    assert access_token.expiration == valid_from + timedelta(seconds=3600)


@pytest.mark.asyncio
async def test_get_user_from_refresh_token(
    token_services: TokenServices, token_repository: AsyncMock, token_user: TokenUser
) -> None:
    token_repository.find_user_by_refresh_token.return_value = token_user
    user = await token_services.get_user_from_refresh_token("refresh_token")
    assert user == token_user


@pytest.mark.asyncio
async def test_get_user_from_access_token(
    token_services: TokenServices,
    token_repository: AsyncMock,
    token_user: TokenUser,
    refresh_token: RefreshToken,
) -> None:
    token_repository.find_user_by_refresh_token_id.return_value = token_user
    valid_from = datetime.now(UTC)
    access_token = token_services.create_access_token(
        token_user, refresh_token, valid_from
    )
    user = await token_services.get_user_from_access_token(access_token.token)
    assert user == token_user


@pytest.mark.asyncio
async def test_get_refresh_token(
    token_services: TokenServices,
    token_repository: AsyncMock,
    refresh_token: RefreshToken,
) -> None:
    token_repository.find_by_token.return_value = refresh_token
    token = await token_services.get_refresh_token("refresh_token")
    assert token == refresh_token


@pytest.mark.asyncio
async def test_create_token_pair(
    token_services: TokenServices, token_repository: AsyncMock, token_user: MagicMock
) -> None:
    token_repository.find_user_by_email.return_value = token_user
    token_user.verify_password = MagicMock(return_value=True)
    token_pair_input = TokenPairInput(email="test@example.com", password="password")
    refresh_token, access_token = await token_services.create_token_pair(
        token_pair_input, valid_from=datetime.now(UTC)
    )
    assert refresh_token.token is not None
    assert access_token.token is not None


@pytest.mark.asyncio
async def test_revoke_refresh_token(
    token_services: TokenServices, token_repository: AsyncMock, token_user: TokenUser
) -> None:
    token_repository.find_user_by_refresh_token.return_value = token_user
    await token_services.revoke_refresh_token("refresh_token")
    token_repository.remove_refresh_token.assert_called_once_with(
        user_id=token_user.id, refresh_token="refresh_token"
    )
