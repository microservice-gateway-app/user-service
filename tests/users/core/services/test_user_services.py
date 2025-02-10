from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from users.core.shared import RoleId, UserId
from users.core.users.domain.profile import Profile
from users.core.users.domain.user import User
from users.core.users.repository import UserRepository
from users.core.users.schemas import (
    UserPasswordChange,
    UserProfileUpdate,
    UserRegister,
)
from users.core.users.services import UserServices


@pytest.fixture
def user_repository() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def user_services(user_repository: AsyncMock) -> UserServices:
    return UserServices(user_repository=user_repository)


@pytest.fixture
def user_admin_create() -> MagicMock:
    return MagicMock(
        email="test@example.com",
        password="password",
        role_ids=[str(uuid4()), str(uuid4())],
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def user() -> MagicMock:
    user = MagicMock(spec=User)
    user.id = MagicMock(value="user_id")
    return user


@pytest.fixture
def profile() -> MagicMock:
    return MagicMock(spec=Profile)


@pytest.mark.asyncio
async def test_register_user(
    user_services: UserServices, user_repository: AsyncMock
) -> None:
    input_data = MagicMock(spec=UserRegister)
    user = MagicMock()
    profile = MagicMock()
    role = AsyncMock()

    input_data.user.return_value = user
    input_data.profile.return_value = profile
    user.assign_role(role)

    user_repository.find_default_role.return_value = role

    await user_services.register_user(input_data)

    user_repository.save_user.assert_called_once_with(user)
    user_repository.save_profile.assert_called_once_with(profile)


@pytest.mark.asyncio
async def test_create_user(
    user_services: UserServices,
    user_repository: AsyncMock,
    user_admin_create: MagicMock,
    user: MagicMock,
    profile: MagicMock,
) -> None:
    user_admin_create.user = MagicMock(return_value=user)
    user_admin_create.profile = MagicMock(return_value=profile)
    user_repository.find_role_by_id.side_effect = [MagicMock(), MagicMock()]

    await user_services.create_user(user_admin_create)

    user_admin_create.user.assert_called_once()
    user_admin_create.profile.assert_called_once_with(user.id)
    assert user.assign_role.call_count == 2
    user_repository.save_user.assert_called_once_with(user)
    user_repository.save_profile.assert_called_once_with(profile)


@pytest.mark.asyncio
async def test_create_user_with_nonexistent_role(
    user_services: UserServices,
    user_repository: AsyncMock,
    user_admin_create: MagicMock,
    user: MagicMock,
    profile: MagicMock,
) -> None:
    user_admin_create.user = MagicMock(return_value=user)
    user_admin_create.profile = MagicMock(return_value=profile)
    user_repository.find_role_by_id.side_effect = [MagicMock(), None]

    await user_services.create_user(user_admin_create)

    user_admin_create.user.assert_called_once()
    user_admin_create.profile.assert_called_once_with(user.id)
    assert user.assign_role.call_count == 1
    user_repository.save_user.assert_called_once_with(user)
    user_repository.save_profile.assert_called_once_with(profile)


@pytest.mark.asyncio
async def test_get_user_profile(
    user_services: UserServices, user_repository: AsyncMock
) -> None:
    user_id = UserId(value=str(uuid4()))
    profile = MagicMock()
    user_repository.find_profile_by_id.return_value = profile
    with patch("users.core.users.services.UserProfileView") as UserProfileView:
        UserProfileView.from_profile.return_value = {}
        result = await user_services.get_user_profile(user_id)
        assert result == {}
    user_repository.find_profile_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_get_user_profile_not_found(
    user_services: UserServices, user_repository: AsyncMock
) -> None:
    user_id = UserId()
    user_repository.find_profile_by_id.return_value = None
    with pytest.raises(
        ValueError, match=f"NOT FOUND: Profile for user {user_id} not found."
    ):
        await user_services.get_user_profile(user_id)


@pytest.mark.asyncio
async def test_update_user_profile(
    user_services: UserServices, user_repository: AsyncMock
) -> None:
    user_id = UserId(value=str(uuid4()))
    input_data = MagicMock(spec=UserProfileUpdate)
    profile = AsyncMock()

    user_repository.find_profile_by_id.return_value = profile
    with patch("users.core.users.services.UserProfileView") as UserProfileView:
        UserProfileView.from_profile.return_value = {}
        result = await user_services.update_user_profile(user_id, input_data)
        assert result == {}
    user_repository.save_profile.assert_called_once()


@pytest.mark.asyncio
async def test_change_password(
    user_services: UserServices, user_repository: AsyncMock
) -> None:
    user_id = UserId(value=str(uuid4()))
    input_data = UserPasswordChange(password="oldpass", new_password="newpass")
    user = AsyncMock()
    user.verify_password.return_value = True

    user_repository.find_user_by_id.return_value = user

    await user_services.change_password(user_id, input_data)
    user.set_password.assert_called_once_with("newpass")
    user_repository.save_user.assert_called_once_with(user)


@pytest.mark.asyncio
async def test_assign_roles(
    user_services: UserServices, user_repository: AsyncMock
) -> None:
    user_id = UserId(value=str(uuid4()))
    role_ids = [RoleId(value=str(uuid4()))]
    user = AsyncMock()
    role = AsyncMock()

    user_repository.find_user_by_id.return_value = user
    user_repository.find_role_by_id.return_value = role

    await user_services.assign_roles(user_id, role_ids)
    user.assign_role.assert_called_once_with(role)
    user_repository.save_user.assert_called_once_with(user)


@pytest.mark.asyncio
async def test_remove_roles(
    user_services: UserServices, user_repository: AsyncMock
) -> None:
    user_id = UserId(value=str(uuid4()))
    role_ids = [RoleId(value=str(uuid4()))]
    user = AsyncMock()
    role = AsyncMock()

    user_repository.find_user_by_id.return_value = user
    user_repository.find_role_by_id.return_value = role

    await user_services.remove_roles(user_id, role_ids)
    user.remove_role.assert_called_once_with(role)
    user_repository.save_user.assert_called_once_with(user)


@pytest.mark.asyncio
async def test_delete_user(
    user_services: UserServices, user_repository: AsyncMock
) -> None:
    user_id = UserId(value=str(uuid4()))
    user = AsyncMock()

    user_repository.find_user_by_id.return_value = user

    await user_services.delete_user(user_id)
    user_repository.delete_user.assert_called_once_with(user.id)
    user_repository.delete_profile.assert_called_once_with(user.id)
