from collections.abc import Collection
from enum import Enum

from pydantic import BaseModel, Field

from ..shared.id import UserId
from .access_user import AccessUser
from .repository import AccessRepository


class UserScope(Enum):
    USER_READ = "users"
    USER_WRITE = "users.write"
    USER_READ_SELF = "users:self"
    USER_WRITE_SELF = "users:self.write"


class Actor(BaseModel):
    user_id: UserId = Field()
    scopes: list[UserScope] = Field(default_factory=list)

    def has_scope(self, scope: UserScope) -> bool:
        return any(s == scope for s in self.scopes)

    def has_any_scope(self, scopes: Collection[UserScope]) -> bool:
        return any(set(self.scopes).intersection(scopes))

    async def to_user(self, repository: AccessRepository) -> AccessUser | None:
        return await repository.find_user_by_id(self.user_id)
