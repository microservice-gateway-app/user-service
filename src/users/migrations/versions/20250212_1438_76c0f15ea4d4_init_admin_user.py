"""init admin user

Revision ID: 76c0f15ea4d4
Revises: 6de16db1b738
Create Date: 2025-02-12 14:38:00.180147

"""

from typing import Sequence
from uuid import uuid4

from alembic import op

from users.config import UserServiceConfigurations
from users.core.users.domain.user import User

# revision identifiers, used by Alembic.
revision: str = "76c0f15ea4d4"
down_revision: str | None = "6de16db1b738"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Insert default roles
    admin_role_id = str(uuid4())
    user_role_id = str(uuid4())
    op.execute(
        f"""
        INSERT INTO roles (id, name) VALUES
        ('{admin_role_id}', 'admin'),
        ('{user_role_id}', 'user')
        """
    )

    # Insert default permissions
    permissions = [
        {"name": "", "namespace": "users", "role_id": admin_role_id},
        {"name": "write", "namespace": "users", "role_id": admin_role_id},
        {"name": "", "namespace": "users:self", "role_id": admin_role_id},
        {"name": "write", "namespace": "users:self", "role_id": admin_role_id},
        {"name": "", "namespace": "users:self", "role_id": user_role_id},
        {"name": "write", "namespace": "users:self", "role_id": user_role_id},
    ]

    for permission in permissions:
        permission_id = str(uuid4())
        op.execute(
            f"""
            INSERT INTO permissions (id, name, namespace) VALUES
            ('{permission_id}', '{permission["name"]}', '{permission["namespace"]}')
            """
        )
        op.execute(
            f"""
            INSERT INTO role_permissions (role_id, permission_id) VALUES
            ('{permission["role_id"]}', '{permission_id}')
            """
        )

    # Insert admin user
    config = UserServiceConfigurations()
    user = User(email=config.ADMIN_EMAIL, password_hash="")
    user.set_password(config.ADMIN_PASSWORD)
    admin_user_id = str(uuid4())
    admin_email = user.email
    admin_password_hash = user.password_hash
    op.execute(
        f"""
        INSERT INTO users (id, email, password_hash) VALUES
        ('{admin_user_id}', '{admin_email}', '{admin_password_hash}')
        """
    )

    # Insert admin profile
    op.execute(
        f"""
        INSERT INTO profiles (
            user_id,
            email,
            first_name,
            last_name,
            phone_number,
            address,
            city,
            state,
            zip_code,
            country,
            avatar,
            bio,
            website,
            birth_date
        ) VALUES (
            '{admin_user_id}',
            '{admin_email}',
            'Admin',
            'User',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            NULL,
            NULL,
            NULL
        )
        """
    )

    # Assign admin role to admin user
    op.execute(
        f"""
        INSERT INTO user_roles (user_id, role_id) VALUES
        ('{admin_user_id}', '{admin_role_id}')
        """
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
