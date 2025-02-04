import uuid
from datetime import UTC, datetime
from typing import Sequence
from unittest.mock import AsyncMock, MagicMock

import pytest

from users.core.domain.permission import Permission, PermissionId
from users.core.domain.role import Role, RoleId
from users.core.domain.user import User, UserId, UserQuery
from users.core.services.user_services import UserRepository, UserServices


@pytest.fixture
def user_repository_mock() -> UserRepository:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def user_service(user_repository_mock: UserRepository) -> UserServices:
    return UserServices(repository=user_repository_mock)


@pytest.fixture
def sample_user() -> User:
    return User(
        id=UserId(value=str(uuid.uuid4())),
        password="1234",
        email="test@example.com",
        first_name="John",
        middle_name="Michael",
        last_name="Doe",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_role() -> Role:
    return Role(id=RoleId(value=str(uuid.uuid4())), name="Admin")


@pytest.fixture
def sample_permission() -> Permission:
    return Permission(id=PermissionId(value=str(uuid.uuid4())), scope_name="read")


@pytest.mark.asyncio
async def test_create_user(
    user_service: UserServices, user_repository_mock: AsyncMock, sample_user: User
):
    user_repository_mock.find_by_email.return_value = None
    user_repository_mock.save.return_value = None
    user_input = MagicMock()
    user_input.to_user.return_value = sample_user
    result = await user_service.create_user(user_input)
    user_repository_mock.save.assert_called_once_with(sample_user)
    assert result == sample_user


@pytest.mark.asyncio
async def test_get_user_by_id(
    user_service: UserServices, user_repository_mock: AsyncMock, sample_user: User
):
    user_repository_mock.find_by_id.return_value = sample_user
    result = await user_service.get_user_by_id(sample_user.id)
    user_repository_mock.find_by_id.assert_called_once_with(sample_user.id)
    assert result == sample_user


@pytest.mark.asyncio
async def test_update_user(
    user_service: UserServices, user_repository_mock: AsyncMock, sample_user: User
):
    user_repository_mock.save.return_value = None
    result = await user_service.update_user(sample_user)
    user_repository_mock.save.assert_called_once_with(sample_user)
    assert result == sample_user


@pytest.mark.asyncio
async def test_delete_user(
    user_service: UserServices, user_repository_mock: AsyncMock, sample_user: User
):
    user_repository_mock.delete.return_value = None
    await user_service.delete_user(sample_user.id)
    user_repository_mock.delete.assert_called_once_with(sample_user.id)


@pytest.mark.asyncio
async def test_assign_role_to_user(
    user_service: UserServices,
    user_repository_mock: AsyncMock,
    sample_user: User,
    sample_role: Role,
):
    user_repository_mock.find_by_id.return_value = sample_user
    user_repository_mock.find_role_by_id.return_value = sample_role
    await user_service.assign_role_to_user(sample_user.id, sample_role.id)
    user_repository_mock.save.assert_called_once()
    print(sample_user.roles)
    assert any(role.id.value == sample_role.id.value for role in sample_user.roles)


@pytest.mark.asyncio
async def test_revoke_role_from_user(
    user_service: UserServices,
    user_repository_mock: AsyncMock,
    sample_user: User,
    sample_role: Role,
):
    sample_user.add_role(sample_role)
    user_repository_mock.find_by_id.return_value = sample_user
    user_repository_mock.find_role_by_id.return_value = sample_role
    await user_service.revoke_role_from_user(sample_user.id, sample_role.id)
    user_repository_mock.save.assert_called_once()
    assert sample_role not in sample_user.roles


@pytest.mark.asyncio
async def test_add_prohibited_permission_to_user(
    user_service: UserServices,
    user_repository_mock: AsyncMock,
    sample_user: User,
    sample_permission: Permission,
):
    user_repository_mock.find_by_id.return_value = sample_user
    user_repository_mock.find_permission_by_id.return_value = sample_permission
    await user_service.add_prohibited_permission_to_user(
        sample_user.id, sample_permission.id
    )
    user_repository_mock.save.assert_called_once()
    assert sample_permission.scope_name in sample_user.prohibited_permissions


@pytest.mark.asyncio
async def test_remove_prohibited_permission_from_user(
    user_service: UserServices,
    user_repository_mock: AsyncMock,
    sample_user: User,
    sample_permission: Permission,
):
    sample_user.add_prohibited_permission(sample_permission)
    user_repository_mock.find_by_id.return_value = sample_user
    user_repository_mock.find_permission_by_id.return_value = sample_permission
    await user_service.remove_prohibited_permission_from_user(
        sample_user.id, sample_permission.id
    )
    user_repository_mock.save.assert_called_once()
    assert sample_permission not in sample_user.prohibited_permissions


@pytest.mark.asyncio
async def test_assign_permission_to_role_new_permission(
    user_service: UserServices,
    user_repository_mock: AsyncMock,
    sample_role: Role,
    sample_permission: Permission,
) -> None:
    """Test assigning a permission to a role when the permission is not already assigned."""

    user_repository_mock.find_role_by_id.return_value = sample_role
    user_repository_mock.find_permission_by_id.return_value = sample_permission

    await user_service.assign_permission_to_role(sample_role.id, sample_permission.id)

    assert sample_permission in sample_role.permissions
    user_repository_mock.save_role.assert_called_once_with(sample_role)


@pytest.mark.asyncio
async def test_assign_permission_to_role_existing_permission(
    user_service: UserServices,
    user_repository_mock: AsyncMock,
    sample_role: Role,
    sample_permission: Permission,
) -> None:
    """Test assigning a permission to a role when the permission already exists (no duplicate added)."""

    sample_role.permissions.append(sample_permission)
    user_repository_mock.find_role_by_id.return_value = sample_role
    user_repository_mock.find_permission_by_id.return_value = sample_permission

    await user_service.assign_permission_to_role(sample_role.id, sample_permission.id)

    assert sample_role.permissions.count(sample_permission) == 1
    user_repository_mock.save_role.assert_not_called()


@pytest.mark.asyncio
async def test_revoke_permission_from_role_existing_permission(
    user_service: UserServices,
    user_repository_mock: AsyncMock,
    sample_role: Role,
    sample_permission: Permission,
) -> None:
    """Test revoking a permission from a role when the permission exists."""

    sample_role.permissions.append(sample_permission)
    user_repository_mock.find_role_by_id.return_value = sample_role
    user_repository_mock.find_permission_by_id.return_value = sample_permission

    await user_service.revoke_permission_from_role(sample_role.id, sample_permission.id)

    assert sample_permission not in sample_role.permissions
    user_repository_mock.save_role.assert_called_once_with(sample_role)


@pytest.mark.asyncio
async def test_revoke_permission_from_role_non_existing_permission(
    user_service: UserServices,
    user_repository_mock: AsyncMock,
    sample_role: Role,
    sample_permission: Permission,
) -> None:
    """Test revoking a permission from a role when the permission does not exist (no action taken)."""

    user_repository_mock.find_role_by_id.return_value = sample_role
    user_repository_mock.find_permission_by_id.return_value = sample_permission

    await user_service.revoke_permission_from_role(sample_role.id, sample_permission.id)

    assert sample_permission not in sample_role.permissions
    user_repository_mock.save_role.assert_not_called()


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(
    user_service: UserServices, user_repository_mock: AsyncMock
) -> None:
    """Test get_user_by_id raises ValueError when user is not found."""
    user_repository_mock.find_by_id.return_value = None

    with pytest.raises(ValueError, match="User with ID .* not found"):
        await user_service.get_user_by_id(UserId(value=str(uuid.uuid4())))


@pytest.mark.asyncio
async def test_get_user_permissions(
    user_service: UserServices, user_repository_mock: AsyncMock
) -> None:
    """Test get_user_permissions to ensure unique permissions are returned."""
    role_1 = Role(id=RoleId(value=str(uuid.uuid4())), name="Role1", permissions=[])
    role_2 = Role(id=RoleId(value=str(uuid.uuid4())), name="Role2", permissions=[])

    permission_1 = Permission(
        id=PermissionId(value=str(uuid.uuid4())), scope_name="READ"
    )
    permission_2 = Permission(
        id=PermissionId(value=str(uuid.uuid4())), scope_name="WRITE"
    )

    role_1.permissions.append(permission_1)
    role_2.permissions.append(permission_1)  # Duplicate permission
    role_2.permissions.append(permission_2)

    user = MagicMock(spec=User)
    user.roles = [role_1, role_2]

    user_repository_mock.find_by_id.return_value = user

    permissions = await user_service.get_user_permissions(
        UserId(value=str(uuid.uuid4()))
    )

    assert len(permissions) == 2  # Ensure unique permissions
    assert permission_1 in permissions
    assert permission_2 in permissions


@pytest.mark.asyncio
async def test_assign_role_to_user_role_already_assigned(
    user_service: UserServices, user_repository_mock: AsyncMock
) -> None:
    """Test assigning a role that is already assigned does not save the user."""
    role = Role(id=RoleId(value=str(uuid.uuid4())), name="Admin", permissions=[])
    user = MagicMock(spec=User)
    user.roles = [role]

    user_repository_mock.find_by_id.return_value = user
    user_repository_mock.find_role_by_id.return_value = role

    await user_service.assign_role_to_user(UserId(value=str(uuid.uuid4())), role.id)

    user.add_role.assert_not_called()
    user_repository_mock.save.assert_not_called()


@pytest.mark.asyncio
async def test_revoke_role_from_user_role_not_assigned(
    user_service: UserServices, user_repository_mock: AsyncMock
) -> None:
    """Test revoking a role that is not assigned does not save the user."""
    role = Role(id=RoleId(value=str(uuid.uuid4())), name="Admin", permissions=[])
    user = MagicMock(spec=User)
    user.roles = []

    user_repository_mock.find_by_id.return_value = user
    user_repository_mock.find_role_by_id.return_value = role

    await user_service.revoke_role_from_user(UserId(value=str(uuid.uuid4())), role.id)

    user.remove_role.assert_not_called()
    user_repository_mock.save.assert_not_called()


@pytest.mark.asyncio
async def test_get_user_roles(
    user_service: UserServices, user_repository_mock: AsyncMock
) -> None:
    """Test get_user_roles returns the correct roles for a given user ID."""
    # Arrange
    user_id: UserId = UserId(value=str(uuid.uuid4()))
    roles: Sequence[Role] = [
        Role(id=RoleId(value=str(uuid.uuid4())), name="Admin", permissions=[]),
        Role(id=RoleId(value=str(uuid.uuid4())), name="User", permissions=[]),
    ]

    user_repository_mock.get_user_roles.return_value = roles

    # Act
    result: Sequence[Role] = await user_service.get_user_roles(user_id)

    # Assert
    assert result == roles
    user_repository_mock.get_user_roles.assert_awaited_once_with(user_id)


@pytest.mark.asyncio
async def test_query_users(
    user_service: UserServices, user_repository_mock: AsyncMock
) -> None:
    """Test query_users returns the correct list of users."""
    # Arrange
    query = UserQuery(page=1, page_size=10)
    users: Sequence[User] = [
        User(
            id=UserId(value=str(uuid.uuid4())),
            email="",
            password="",
            first_name="",
            last_name="",
            created_at=datetime.now(UTC),
            roles=[],
            prohibited_permissions=[],
        )
    ]
    total = 1

    user_repository_mock.query_users.return_value = (users, total)

    # Act
    result = await user_service.query_users(query)

    # Assert
    assert result.users == users
    assert result.total == total
    assert result.page == query.page
    assert result.page_size == query.page_size
    assert result.total_pages == 1
    user_repository_mock.query_users.assert_awaited_once_with(query)
