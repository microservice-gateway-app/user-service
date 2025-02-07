from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ...shared.uuid import UUID


class Token(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    token: str
    token_type: str
    expiration: datetime


class RefreshTokenId(UUID, frozen=True): ...


class RefreshToken(Token):
    model_config = ConfigDict(from_attributes=True)

    token_type: str = "refresh"
    id: RefreshTokenId = Field(default_factory=RefreshTokenId)
    user_id: str


class TokenExtra(BaseModel):
    user_id: str | None = None
    scopes: list[str] = Field(default_factory=list)


class AccessToken(Token):
    model_config = ConfigDict(from_attributes=True)

    token_type: str = "access"
    data: TokenExtra | None = None

    def belongs_to_user(self, user_id: str) -> bool:
        return bool(self.data and self.data.user_id == user_id)

    def has_scope(self, scope: str) -> bool:
        return bool(self.data and scope in self.data.scopes)


class PasswordResetToken(Token):
    model_config = ConfigDict(from_attributes=True)

    token_type: str = "password_reset"
    data: TokenExtra | None = None

    def belongs_to_user(self, user_id: str) -> bool:
        return bool(self.data and self.data.user_id == user_id)
