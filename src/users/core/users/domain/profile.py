from pydantic import BaseModel, ConfigDict

from ...shared import UserId


class Profile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UserId
    email: str
    # necessary fields for a normal profile
    first_name: str
    last_name: str
    phone_number: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    # optional fields
    avatar: str | None = None
    bio: str | None = None
    website: str | None = None
    birth_date: str | None = None
