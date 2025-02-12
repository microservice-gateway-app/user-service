from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import case

from .base import Base


class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None
    )

    def soft_delete(self):
        self.deleted_at = datetime.now(UTC)


class UserORM(Base, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    profile: Mapped[ProfileORM] = relationship("ProfileORM", back_populates="user")
    roles: Mapped[list[RoleORM]] = relationship(
        secondary="user_roles", back_populates="users", lazy="selectin"
    )


class ProfileORM(Base, SoftDeleteMixin):
    __tablename__ = "profiles"

    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), primary_key=True
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    zip_code: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    birth_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user: Mapped[UserORM] = relationship("UserORM", back_populates="profile")


class RoleORM(Base, SoftDeleteMixin):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    users: Mapped[list[UserORM]] = relationship(
        secondary="user_roles", back_populates="roles", lazy="selectin"
    )

    permissions: Mapped[list[PermissionORM]] = relationship(
        secondary="role_permissions", back_populates="roles", lazy="selectin"
    )


class UserRoleORM(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), primary_key=True)


class PermissionORM(Base, SoftDeleteMixin):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    namespace: Mapped[str] = mapped_column(String, nullable=False)

    roles: Mapped[list[RoleORM]] = relationship(
        secondary="role_permissions", back_populates="permissions", lazy="selectin"
    )

    @hybrid_property
    def full_name(self) -> str:
        """Returns namespace if name is empty, otherwise 'namespace.name'."""
        return self.namespace if not self.name else f"{self.namespace}.{self.name}"

    @full_name.inplace.expression
    @classmethod
    def full_name_expr(cls):
        """SQL version of full_name property."""
        return case(
            (cls.name == "", cls.namespace),  # If name is an empty string
            (cls.name.is_(None), cls.namespace),  # If name is NULL
            else_=cls.namespace + "." + cls.name,  # Default case
        )


class RolePermissionORM(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[str] = mapped_column(ForeignKey("permissions.id"), primary_key=True)


class RefreshTokenRecord(Base, SoftDeleteMixin):
    __tablename__ = "refresh_tokens"
    id: Mapped[str] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(unique=True)
    expiration: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
