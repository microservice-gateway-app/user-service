import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from jose import JWTError, jwt

from users.config import UserServiceConfigurations
from users.core.domain.token import AccessToken, RefreshToken, RefreshTokenId
from users.core.domain.user import User, UserId
from users.core.services.token_services import TokenPairInput, TokenServices
from users.core.services.user_services import hash_password


@pytest.fixture
def mock_user_repository() -> AsyncMock:
    """Mock the user repository."""
    return AsyncMock()


@pytest.fixture
def mock_token_repository() -> AsyncMock:
    """Mock the token repository."""
    return AsyncMock()


@pytest.fixture
def mock_config() -> UserServiceConfigurations:
    """Mock the configuration."""
    config = MagicMock()
    config.REFRESH_TOKEN_TTL_DAYS = 7
    config.ACCESS_TOKEN_TTL_SECONDS = 3600  # 1 hour
    config.SECRET_KEY = "test_secret"
    config.ALGORITHM = "HS256"
    return config


@pytest.fixture
def token_service(
    mock_user_repository: AsyncMock,
    mock_token_repository: AsyncMock,
    mock_config: MagicMock,
) -> TokenServices:
    """Instantiate the TokenServices with mocked dependencies."""
    return TokenServices(
        user_repository=mock_user_repository,
        token_repository=mock_token_repository,
        config=mock_config,
    )


@pytest.mark.asyncio
async def test_create_refresh_token(
    token_service: TokenServices, mock_token_repository: AsyncMock
):
    """Test the create_refresh_token method."""
    user = MagicMock(id=UserId(value=str(uuid.uuid4())))
    valid_from = datetime.now(UTC)

    # Call the method to test
    refresh_token = await token_service.create_refresh_token(user, valid_from)

    # Verify that the refresh token is created correctly
    assert refresh_token.user_id == user.id.value
    assert refresh_token.expiration > valid_from
    assert isinstance(refresh_token.token, str)
    mock_token_repository.save_refresh_token.assert_awaited_once_with(refresh_token)


@pytest.mark.asyncio
async def test_create_access_token(
    token_service: TokenServices, mock_config: MagicMock
):
    """Test the create_access_token method."""
    refresh_token = RefreshToken(
        token="some_refresh_token",
        expiration=datetime.now(UTC) + timedelta(days=7),
        user_id=str(uuid.uuid4()),
    )
    valid_from = datetime.now(UTC)

    # Call the method to test
    user = MagicMock(
        id=UserId(value=refresh_token.user_id),
        roles=[],
        prohibited_permissions=[],
    )
    access_token = token_service.create_access_token(
        refresh_token=refresh_token, valid_from=valid_from, user=user
    )

    # Verify that the access token is created correctly
    assert access_token.token is not None
    assert access_token.expiration > valid_from
    assert "sub" in jwt.decode(
        access_token.token, mock_config.SECRET_KEY, algorithms=[mock_config.ALGORITHM]
    )


@pytest.mark.asyncio
async def test_get_user_from_access_token(
    token_service: TokenServices,
    mock_user_repository: AsyncMock,
    mock_config: UserServiceConfigurations,
):
    """Test retrieving the user from the access token."""
    user = MagicMock(id=UserId(value=str(uuid.uuid4())))
    token_id = str(uuid.uuid4())
    token = jwt.encode(
        {
            "sub": token_id,
            "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
        },
        mock_config.SECRET_KEY,
        algorithm=mock_config.ALGORITHM,
    )

    # Mock the repository to return the user
    mock_user_repository.find_by_refresh_token_id.return_value = user

    # Call the method to test
    result = await token_service.get_user_from_access_token(token)

    # Verify that the correct user is returned
    assert result == user
    mock_user_repository.find_by_refresh_token_id.assert_awaited_once_with(
        RefreshTokenId(value=token_id)
    )


@pytest.mark.asyncio
async def test_get_user_from_invalid_access_token(
    token_service: TokenServices,
    mock_user_repository: AsyncMock,
    mock_config: UserServiceConfigurations,
):
    """Test error handling for invalid access token."""
    token = jwt.encode(
        {
            "sub": "12345",
            "exp": (datetime.now(UTC) - timedelta(hours=1)).timestamp(),
        },  # Expired token
        mock_config.SECRET_KEY,
        algorithm=mock_config.ALGORITHM,
    )

    # Mock repository
    mock_user_repository.find_by_id.return_value = None

    # Call the method to test, expecting an exception
    with pytest.raises(JWTError):
        await token_service.get_user_from_access_token(token)


@pytest.mark.asyncio
async def test_create_token_pair(
    token_service: TokenServices, mock_user_repository: AsyncMock
):
    """Test the create_token_pair method."""
    password = "1234"
    token_pair_input = TokenPairInput(
        password=password,
        email="test@example.com",
    )
    valid_from = datetime.now(UTC)
    mock_user = MagicMock(id=UserId(), password=hash_password(password))
    mock_user_repository.find_by_email.return_value = mock_user

    # Call the method to test
    refresh_token, access_token = await token_service.create_token_pair(
        token_pair_input, valid_from
    )

    # Verify both tokens are created
    assert isinstance(refresh_token, RefreshToken)
    assert isinstance(access_token, AccessToken)
    assert access_token.expiration > valid_from


@pytest.mark.asyncio
async def test_get_user_from_expired_access_token(
    token_service: TokenServices,
    mock_config: UserServiceConfigurations,
) -> None:
    """Test that an expired access token raises an error."""
    user_id = uuid.uuid4()  # Use UUID
    expired_token = jwt.encode(
        {
            "sub": str(user_id),
            "exp": (datetime.now(UTC) - timedelta(seconds=1)).timestamp(),
        },
        mock_config.SECRET_KEY,
        algorithm=mock_config.ALGORITHM,
    )

    # Call the method to test, expecting an exception
    with pytest.raises(JWTError):
        await token_service.get_user_from_access_token(expired_token)


@pytest.mark.asyncio
async def test_get_user_from_invalid_access_token_payload(
    token_service: TokenServices,
) -> None:
    """Test that an error is raised if the access token has an invalid payload."""
    # Malformed JWT (missing exp or sub)
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX3N0b3J5In0.-Ldr6z-Q4hP2Gf61KtbZJ7LC8-EXz0m3GRzflkM5zjo"

    # Call the method to test, expecting an exception
    with pytest.raises(JWTError):
        await token_service.get_user_from_access_token(invalid_token)


@pytest.mark.asyncio
async def test_get_user_from_access_token_missing_sub(
    token_service: TokenServices,
    mock_config: UserServiceConfigurations,
) -> None:
    """Test that an error is raised when the access token is missing 'sub' (user ID)."""
    # Malformed JWT (missing sub)
    invalid_token = jwt.encode(
        {"exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp()},
        mock_config.SECRET_KEY,
        algorithm=mock_config.ALGORITHM,
    )
    # Call the method to test, expecting an exception
    with pytest.raises(JWTError):
        await token_service.get_user_from_access_token(invalid_token)


# Test get_user_from_refresh_token
@pytest.mark.asyncio
async def test_get_user_from_refresh_token(
    token_service: TokenServices, mock_user_repository: MagicMock
):
    refresh_token = "some-refresh-token"
    user = User(
        id=UserId(value=str(uuid.uuid4())),
        email="test@example.com",
        password="1234",
        first_name="John",
        middle_name="Michael",
        last_name="Doe",
        created_at=datetime.now(UTC),
    )
    mock_user_repository.find_by_refresh_token.return_value = user

    result = await token_service.get_user_from_refresh_token(refresh_token)

    assert result == user
    mock_user_repository.find_by_refresh_token.assert_called_once_with(
        refresh_token=refresh_token
    )


@pytest.mark.asyncio
async def test_get_refresh_token_not_found(
    token_service: TokenServices, mock_token_repository: AsyncMock
):
    """Test that get_refresh_token raises an error when the token is not found."""
    mock_token_repository.find_by_token.return_value = None

    with pytest.raises(ValueError, match="Token not found"):
        await token_service.get_refresh_token("invalid-token")


@pytest.mark.asyncio
async def test_revoke_refresh_token_not_found(
    token_service: TokenServices, mock_user_repository: AsyncMock
):
    """Test that revoke_refresh_token raises an error when the token is not found."""
    mock_user_repository.find_by_refresh_token.return_value = None

    with pytest.raises(ValueError, match="Refresh token not found"):
        await token_service.revoke_refresh_token("invalid-refresh-token")


@pytest.mark.asyncio
async def test_revoke_refresh_token_error_handling(
    token_service: TokenServices, mock_user_repository: AsyncMock
):
    """Test revoke_refresh_token handles unexpected errors correctly."""
    mock_user_repository.find_by_refresh_token.side_effect = Exception("DB error")

    with pytest.raises(ValueError, match="Error revoking refresh token: DB error"):
        await token_service.revoke_refresh_token("some-refresh-token")


@pytest.mark.asyncio
async def test_create_token_pair_invalid_password(
    token_service: TokenServices, mock_user_repository: AsyncMock
):
    """Test that create_token_pair raises an error for an invalid password."""
    mock_user = MagicMock(id=UserId(), password=hash_password("correct_password"))
    mock_user_repository.find_by_email.return_value = mock_user

    token_pair_input = TokenPairInput(
        email="test@example.com", password="wrong_password"
    )

    with pytest.raises(ValueError, match="Incorrect username or password."):
        await token_service.create_token_pair(token_pair_input)


@pytest.mark.asyncio
async def test_create_token_pair_user_not_found(
    token_service: TokenServices, mock_user_repository: AsyncMock
):
    """Test that create_token_pair raises an error when the user is not found."""
    mock_user_repository.find_by_email.return_value = None

    token_pair_input = TokenPairInput(email="unknown@example.com", password="1234")

    with pytest.raises(ValueError, match="Incorrect username or password."):
        await token_service.create_token_pair(token_pair_input)
