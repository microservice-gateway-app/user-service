from __future__ import annotations

from pydantic import BaseModel, Field

from ..shared import UserId
from .domain.profile import Profile
from .domain.user import User


class UserRegister(BaseModel):
    """Necessary fields for registering a new user and its Profile."""

    email: str
    password: str
    first_name: str
    last_name: str
    phone_number: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    avatar: str | None = None
    bio: str | None = None
    website: str | None = None
    birth_date: str | None = None

    def user(self) -> User:
        return User(
            email=self.email,
            password_hash=self.password,
        )

    def profile(self, user_id: UserId) -> Profile:
        return Profile(
            user_id=user_id,
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            phone_number=self.phone_number,
            address=self.address,
            city=self.city,
            state=self.state,
            zip_code=self.zip_code,
            country=self.country,
            avatar=self.avatar,
            bio=self.bio,
            website=self.website,
            birth_date=self.birth_date,
        )


class UserAdminCreate(UserRegister):
    """Admin user creation model."""

    role_ids: list[str] = Field(default_factory=list)


class UserPasswordChange(BaseModel):
    """Password change model."""

    password: str
    new_password: str


class UserProfileUpdate(BaseModel):
    """Profile update model."""

    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    avatar: str | None = None
    bio: str | None = None
    website: str | None = None
    birth_date: str | None = None

    def apply(self, profile: Profile) -> Profile:
        return Profile(
            user_id=profile.user_id,
            email=profile.email,
            first_name=self.first_name or profile.first_name,
            last_name=self.last_name or profile.last_name,
            phone_number=self.phone_number or profile.phone_number,
            address=self.address or profile.address,
            city=self.city or profile.city,
            state=self.state or profile.state,
            zip_code=self.zip_code or profile.zip_code,
            country=self.country or profile.country,
            avatar=self.avatar or profile.avatar,
            bio=self.bio or profile.bio,
            website=self.website or profile.website,
            birth_date=self.birth_date or profile.birth_date,
        )


class UserQuery(BaseModel):
    """Conditions to filter a list of users."""

    email_like: str | None = None
    name_like: str | None = None
    role_ids: list[str] | None = None

    page: int = 1
    page_size: int = 10


class UserProfileView(BaseModel):
    """Profile view model."""

    user_id: UserId
    first_name: str
    last_name: str
    phone_number: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    avatar: str | None = None
    bio: str | None = None
    website: str | None = None
    birth_date: str | None = None

    @staticmethod
    def from_profile(profile: Profile) -> UserProfileView:
        return UserProfileView(
            user_id=profile.user_id,
            first_name=profile.first_name,
            last_name=profile.last_name,
            phone_number=profile.phone_number,
            address=profile.address,
            city=profile.city,
            state=profile.state,
            zip_code=profile.zip_code,
            country=profile.country,
            avatar=profile.avatar,
            bio=profile.bio,
            website=profile.website,
            birth_date=profile.birth_date,
        )


class UserDetailedProfileView(UserProfileView):
    roles: list[str] = []
    permissions: set[str] = set()


class UserList(BaseModel):
    """List of users."""

    total: int
    page: int
    page_size: int
    users: list[UserProfileView]

    @staticmethod
    def from_profiles(
        profiles: list[Profile], total: int, query: UserQuery
    ) -> UserList:
        return UserList(
            total=total,
            page=query.page,
            page_size=query.page_size,
            users=[UserProfileView.from_profile(profile) for profile in profiles],
        )
