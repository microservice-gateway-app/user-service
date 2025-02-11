from pydantic import BaseModel, ConfigDict, Field

from ...shared import RoleId
from .permission import Permission


class Role(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: RoleId = Field(
        default_factory=RoleId, description="The unique identifier of the role."
    )
    name: str = Field(description="The name of the role.")
    permissions: set[Permission] = Field(default_factory=set)
