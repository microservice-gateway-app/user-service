import bcrypt
from pydantic import BaseModel, ConfigDict, Field

from ...shared import UserId
from .role import Role


class UserRole(BaseModel):
    user_id: UserId
    role: Role


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UserId = Field(default_factory=UserId, description="User's unique ID")
    email: str = Field(description="The user's email.")
    password_hash: str = Field(description="The hashed password.")
    roles: list[UserRole] = Field(default_factory=list)

    def check_password_strength(self, password: str) -> str:
        # check if password is strong enough
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit.")
        if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/~" for c in password):
            raise ValueError("Password must contain at least one special character.")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter.")
        if len(password) > 128:
            raise ValueError("Password must be at most 128 characters long.")
        return password

    def set_password(self, password: str):
        """Hashes and stores the password securely."""
        self.password_hash = bcrypt.hashpw(
            password=self.check_password_strength(password).encode(),
            salt=bcrypt.gensalt(),
        ).decode()

    def verify_password(self, password: str) -> bool:
        """Verifies the password against the stored hash."""
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def assign_role(self, role: Role):
        """Assigns a role to the user."""
        self.roles.append(UserRole(user_id=self.id, role=role))

    def remove_role(self, role: Role):
        """Removes a role from the user."""
        self.roles = [r for r in self.roles if r.role != role]

    def get_permissions(self) -> set[str]:
        """Aggregate namespaced permissions from all assigned roles."""
        permissions = set[str]()
        for user_role in self.roles:
            permissions.update(p.full_name for p in user_role.role.permissions)
        return permissions

    def has_permission(self, permission: str) -> bool:
        """Checks if the user has a specific permission."""
        return permission in self.get_permissions()
