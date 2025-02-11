from pydantic import BaseModel, ConfigDict, Field


class Permission(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    name: str = Field(description="The name of the permission.")
    namespace: str = Field(description="The namespace of the permission.")

    @property
    def full_name(self) -> str:
        return f"{self.namespace}.{self.name}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            return False
        return self.name == other.name and self.namespace == other.namespace

    def __hash__(self) -> int:
        return hash((self.name, self.namespace))
