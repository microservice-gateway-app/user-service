from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from users.core.roles import (
    RoleInput,
    RolePermissionAssignmentInput,
    RoleRepository,
    RoleServices,
)
from users.core.roles.domain import Permission, Role
from users.core.shared import RoleId


@pytest.fixture
def mock_role_repository() -> AsyncMock:
    return AsyncMock(spec=RoleRepository)


@pytest.fixture
def role_service(mock_role_repository: AsyncMock) -> RoleServices:
    return RoleServices(role_repository=mock_role_repository)


def passthrough_fn(_: Any) -> Any:
    return _


@pytest.mark.asyncio
async def test_create_role_with_new_permissions(
    role_service: RoleServices, mock_role_repository: AsyncMock
) -> None:
    role_input = RoleInput(name="Admin", permissions={"users.create", "users.delete"})

    mock_role_repository.find_permission.return_value = None
    mock_role_repository.ensure_permission_exists.side_effect = passthrough_fn

    role_view = await role_service.create_role(role_input)

    assert role_view.name == "Admin"
    assert len(role_view.permissions) == 2
    mock_role_repository.save.assert_called_once()


@pytest.mark.asyncio
async def test_create_role_with_existing_permissions(
    role_service: RoleServices, mock_role_repository: AsyncMock
) -> None:
    role_input = RoleInput(
        name="Editor", permissions={"articles.write", "articles.read"}
    )

    def find_permission_side_effect(namespace: str, name: str) -> Permission:
        return Permission(namespace=namespace, name=name)

    mock_role_repository.find_permission.side_effect = find_permission_side_effect

    role_view = await role_service.create_role(role_input)

    assert role_view.name == "Editor"
    assert len(role_view.permissions) == 2
    mock_role_repository.save.assert_called_once()


@pytest.mark.asyncio
async def test_get_existing_role(
    role_service: RoleServices, mock_role_repository: AsyncMock
) -> None:
    role_id = RoleId(value=str(uuid4()))
    role = Role(id=role_id, name="Admin", permissions=set())
    mock_role_repository.find_by_id.return_value = role

    role_view = await role_service.get_role(role_id)

    assert role_view is not None
    assert role_view.name == "Admin"
    mock_role_repository.find_by_id.assert_called_once_with(role_id)


@pytest.mark.asyncio
async def test_get_non_existing_role(
    role_service: RoleServices, mock_role_repository: AsyncMock
) -> None:
    role_id = RoleId(value=str(uuid4()))
    mock_role_repository.find_by_id.return_value = None

    role_view = await role_service.get_role(role_id)

    assert role_view is None
    mock_role_repository.find_by_id.assert_called_once_with(role_id)


@pytest.mark.asyncio
async def test_delete_existing_role(
    role_service: RoleServices, mock_role_repository: AsyncMock
) -> None:
    role_id = RoleId(value=str(uuid4()))
    role = Role(id=role_id, name="Admin", permissions=set())
    mock_role_repository.find_by_id.return_value = role

    result = await role_service.delete_role(role_id)

    assert result is True
    mock_role_repository.delete.assert_called_once_with(role)


@pytest.mark.asyncio
async def test_delete_non_existing_role(
    role_service: RoleServices, mock_role_repository: AsyncMock
) -> None:
    role_id = RoleId(value=str(uuid4()))
    mock_role_repository.find_by_id.return_value = None

    result = await role_service.delete_role(role_id)

    assert result is False
    mock_role_repository.delete.assert_not_called()


@pytest.mark.asyncio
async def test_assign_permission_to_role(
    role_service: RoleServices, mock_role_repository: AsyncMock
) -> None:
    role_id = RoleId(value=str(uuid4()))
    permission = Permission(namespace="users", name="edit")
    role = Role(id=role_id, name="User", permissions=set())

    mock_role_repository.find_by_id.return_value = role
    mock_role_repository.ensure_permission_exists.return_value = permission

    input_data = RolePermissionAssignmentInput(role_id=role_id, permission=permission)
    result = await role_service.assign_permission_to_role(input_data)

    assert result is True
    assert permission in role.permissions
    mock_role_repository.save.assert_called_once_with(role)


@pytest.mark.asyncio
async def test_remove_permission_from_role(
    role_service: RoleServices, mock_role_repository: AsyncMock
) -> None:
    role_id = RoleId(value=str(uuid4()))
    permission = Permission(namespace="users", name="edit")
    role = Role(id=role_id, name="User", permissions={permission})

    mock_role_repository.find_by_id.return_value = role
    mock_role_repository.any_role_uses_permission.return_value = False

    input_data = RolePermissionAssignmentInput(role_id=role_id, permission=permission)
    result = await role_service.remove_permission_from_role(input_data)

    assert result is True
    assert permission not in role.permissions
    mock_role_repository.ensure_permission_deleted.assert_called_once_with(permission)
    mock_role_repository.save.assert_called_once_with(role)


@pytest.mark.asyncio
async def test_remove_permission_from_role_still_used(
    role_service: RoleServices, mock_role_repository: AsyncMock
) -> None:
    role_id = RoleId(value=str(uuid4()))
    permission = Permission(namespace="users", name="edit")
    role = Role(id=role_id, name="User", permissions={permission})

    mock_role_repository.find_by_id.return_value = role
    mock_role_repository.any_role_uses_permission.return_value = True

    input_data = RolePermissionAssignmentInput(role_id=role_id, permission=permission)
    result = await role_service.remove_permission_from_role(input_data)

    assert result is True
    assert permission not in role.permissions
    mock_role_repository.ensure_permission_deleted.assert_not_called()
    mock_role_repository.save.assert_called_once_with(role)
