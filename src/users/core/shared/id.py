from .uuid import UUID


class UserId(UUID, frozen=True): ...


class RoleId(UUID, frozen=True): ...
