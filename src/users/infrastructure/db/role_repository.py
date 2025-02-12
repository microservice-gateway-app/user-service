from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import delete, select

from users.core.roles import RoleRepository
from users.core.roles.domain import Permission, Role
from users.core.shared import RoleId

from .base import BaseRepository
from .orm import PermissionORM, RoleORM


class RoleRepositoryOnSQLA(RoleRepository, BaseRepository):
    async def find_by_id(self, role_id: RoleId) -> Role | None:
        stmt = (
            select(RoleORM)
            .options(selectinload(RoleORM.permissions))
            .filter_by(id=role_id.value)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        return self._map_to_domain(record) if record else None

    async def find_all(self) -> list[Role]:
        stmt = select(RoleORM).options(selectinload(RoleORM.permissions))
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        return [self._map_to_domain(record) for record in records]

    async def save(self, role: Role) -> None:
        try:
            role_model = RoleORM(
                id=role.id.value,
                name=role.name,
                permissions=[
                    PermissionORM(namespace=perm.namespace, name=perm.name)
                    for perm in role.permissions
                ],
            )
            await self.session.merge(role_model)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error saving role: {str(e)}")

    async def delete(self, role: Role) -> None:
        try:
            stmt = delete(RoleORM).where(RoleORM.id == role.id.value)
            await self.session.execute(stmt)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error deleting role: {str(e)}")

    async def find_permission(self, namespace: str, name: str) -> Permission | None:
        stmt = select(PermissionORM).filter_by(namespace=namespace, name=name)
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        return (
            Permission(namespace=record.namespace, name=record.name) if record else None
        )

    async def ensure_permission_exists(self, permission: Permission) -> Permission:
        existing = await self.find_permission(permission.namespace, permission.name)
        if existing:
            return existing

        try:
            perm_model = PermissionORM(
                namespace=permission.namespace, name=permission.name
            )
            self.session.add(perm_model)
            await self.session.commit()
            return permission
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error ensuring permission exists: {str(e)}")

    async def ensure_permission_deleted(self, permission: Permission) -> None:
        try:
            stmt = delete(PermissionORM).where(
                PermissionORM.namespace == permission.namespace,
                PermissionORM.name == permission.name,
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error deleting permission: {str(e)}")

    async def any_role_uses_permission(self, permission: Permission) -> bool:
        stmt = (
            select(RoleORM)
            .join(RoleORM.permissions)
            .filter(
                PermissionORM.namespace == permission.namespace,
                PermissionORM.name == permission.name,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    def _map_to_domain(self, record: RoleORM) -> Role:
        return Role(
            id=RoleId(value=record.id),
            name=record.name,
            permissions={
                Permission(namespace=p.namespace, name=p.name)
                for p in record.permissions
            },
        )
