from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from sqlalchemy.sql import select

from users.core.domain.token import RefreshTokenId
from users.db.token_repository import RefreshTokenRecord

from ..core.domain.permission import Permission, PermissionId
from ..core.domain.role import Role, RoleId
from ..core.domain.user import User, UserId
from ..core.services.user_repository import UserRepository
from .base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    first_name: Mapped[str] = mapped_column(nullable=False)
    middle_name: Mapped[str | None] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    # Define the relationship with roles
    roles: Mapped[list[RoleModel]] = relationship(
        "RoleModel", secondary="user_roles", lazy="selectin"
    )
    refresh_tokens: Mapped[list[RefreshTokenRecord]] = relationship(
        "RefreshTokenRecord", lazy="selectin"
    )

    # This method allows conversion of a UserModel instance to a domain User
    def to_user(self) -> User:
        """Convert this ORM UserModel to the domain User class."""
        return User(
            id=UserId(value=self.id),
            password=self.password,
            email=self.email,
            first_name=self.first_name,
            middle_name=self.middle_name,
            last_name=self.last_name,
            created_at=self.created_at,
            roles=[role.to_role() for role in self.roles],
            prohibited_permissions=[],  # You can add this logic if needed
        )


# Role ORM Model
class RoleModel(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)

    # Conversion to Role domain model
    def to_role(self) -> Role:
        """Convert this ORM RoleModel to the domain Role class."""
        return Role(id=RoleId(value=self.id), name=self.name)


# Permission ORM Model
class PermissionModel(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(primary_key=True)
    scope_name: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str] = mapped_column(nullable=True)

    # Relationship to roles
    roles = relationship("RoleModel", secondary="role_permissions", lazy="selectin")

    def to_permission(self) -> Permission:
        return Permission(
            id=PermissionId(value=self.id),
            scope_name=self.scope_name,
            description=self.description,
        )


# UserRoles Association Table
class UserRoleModel(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)


# RolePermissions Association Table
class RolePermissionModel(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id"), primary_key=True
    )


class UserRepositoryOnSQLA(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_refresh_token(self, refresh_token: str) -> User | None:
        """Find a user by their refresh token."""
        stmt = select(UserModel).filter(RefreshTokenRecord.token == refresh_token)
        result = await self.session.execute(stmt)
        user_model = result.scalars().first()
        if user_model:
            return user_model.to_user()
        return None

    async def find_by_refresh_token_id(
        self, refresh_token_id: RefreshTokenId
    ) -> User | None:
        """Find a user by their refresh token."""
        stmt = select(UserModel).filter(RefreshTokenRecord.id == refresh_token_id.value)
        result = await self.session.execute(stmt)
        user_model = result.scalars().first()
        if user_model:
            return user_model.to_user()
        return None

    async def find_by_id(self, id: UserId) -> User | None:
        """Find a user by their ID."""
        stmt = (
            select(UserModel)
            .filter(UserModel.id == id.value)
            .options(selectinload(UserModel.roles))
        )
        result = await self.session.execute(stmt)
        user_model = result.scalars().first()
        if user_model:
            return user_model.to_user()
        return None

    async def find_by_email(self, email: str) -> User | None:
        """Find a user by email + password."""
        stmt = select(UserModel).filter_by(email=email)
        result = await self.session.execute(stmt)
        user_model = result.scalars().first()
        if user_model:
            return user_model.to_user()
        return None

    async def save(self, user: User) -> None:
        """Save a new user to the database."""
        try:
            user_model = UserModel(
                id=user.id.value,
                email=user.email,
                first_name=user.first_name,
                middle_name=user.middle_name,
                last_name=user.last_name,
                created_at=user.created_at,
            )
            self.session.add(user_model)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error saving user: {str(e)}")

    async def update(self, user: User) -> None:
        """Update an existing user."""
        try:
            stmt = select(UserModel).filter(UserModel.id == user.id.value)
            result = await self.session.execute(stmt)
            user_model = result.scalars().first()
            if user_model:
                user_model.email = user.email
                user_model.first_name = user.first_name
                user_model.middle_name = user.middle_name
                user_model.last_name = user.last_name
                user_model.created_at = user.created_at
                await self.session.commit()
            else:
                raise ValueError("User not found.")
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error updating user: {str(e)}")

    async def delete(self, user_id: UserId) -> None:
        """Delete a user from the database."""
        try:
            stmt = select(UserModel).filter(UserModel.id == user_id.value)
            result = await self.session.execute(stmt)
            user_model = result.scalars().first()
            if user_model:
                await self.session.delete(user_model)
                await self.session.commit()
            else:
                raise ValueError("User not found.")
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error deleting user: {str(e)}")

    async def get_user_roles(self, user_id: UserId) -> Sequence[Role]:
        """Get all roles of a user."""
        stmt = (
            select(RoleModel)
            .join(UserRoleModel)
            .filter(UserRoleModel.user_id == user_id.value)
        )
        result = await self.session.execute(stmt)
        roles = result.scalars().all()
        return [role.to_role() for role in roles]

    async def get_user_permissions(self, user_id: UserId) -> Sequence[Permission]:
        """Get all permissions of a user."""
        stmt = (
            select(PermissionModel)
            .join(RolePermissionModel)
            .join(UserRoleModel)
            .filter(UserRoleModel.user_id == user_id.value)
        )
        result = await self.session.execute(stmt)
        permissions = result.scalars().all()
        return [permission.to_permission() for permission in permissions]

    async def add_role(self, user: User, role: Role) -> None:
        """Add a role to a user."""
        stmt = select(UserModel).filter(UserModel.id == user.id.value)
        result = await self.session.execute(stmt)
        user_model = result.scalars().first()

        if user_model:
            # Convert the domain Role object to the ORM RoleModel object
            role_result = await self.session.execute(
                select(RoleModel).filter(RoleModel.id == role.id.value)
            )
            role_model = role_result.scalars().first()

            if not role_model:
                raise ValueError("Role not found.")

            # Append the RoleModel object to the user roles relationship
            user_model.roles.append(role_model)
            await self.session.commit()
        else:
            raise ValueError("User not found.")

    async def remove_role(self, user: User, role: Role) -> None:
        """Remove a role from a user."""
        stmt = select(UserModel).filter(UserModel.id == user.id.value)
        result = await self.session.execute(stmt)
        user_model = result.scalars().first()
        if user_model:
            r = next((r for r in user_model.roles if r.id == role.id), None)
            if r:
                user_model.roles.remove(r)
            await self.session.commit()
        else:
            raise ValueError("User not found.")

    async def save_role(self, role: Role) -> None:
        """Save a role to the database."""
        try:
            role_model = RoleModel(name=role.name)
            self.session.add(role_model)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise Exception(f"Error saving role: {str(e)}")

    async def find_role_by_id(self, role_id: RoleId) -> Role:
        """Find a role by its ID."""
        stmt = select(RoleModel).filter(RoleModel.id == role_id.value)
        result = await self.session.execute(stmt)
        role_model = result.scalars().first()
        if role_model:
            return role_model.to_role()
        raise ValueError(f"Role with ID {role_id.value} not found.")

    async def find_permission_by_id(self, permission_id: PermissionId) -> Permission:
        """Find a permission by its ID."""
        stmt = select(PermissionModel).filter(PermissionModel.id == permission_id.value)
        result = await self.session.execute(stmt)
        permission_model = result.scalars().first()
        if permission_model:
            return permission_model.to_permission()
        raise ValueError(f"Permission with ID {permission_id.value} not found.")
