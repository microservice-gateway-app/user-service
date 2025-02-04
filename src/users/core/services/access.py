from collections.abc import Collection
from enum import Enum

from pydantic import BaseModel, Field

from users.core.services.user_repository import UserRepository

from ..domain.user import User, UserId


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

    async def to_user(self, repository: UserRepository) -> User | None:
        return await repository.find_by_id(self.user_id)
