import bcrypt
from pydantic import BaseModel, ConfigDict, Field

from ...shared import UserId


class TokenUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UserId = Field(default_factory=UserId)
    scopes: list[str] = Field(default_factory=list)
    password_hash: str = Field(description="The hashed password.")

    def verify_password(self, password: str) -> bool:
        """Verifies the password against the stored hash."""
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())
