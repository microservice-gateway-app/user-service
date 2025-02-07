from pydantic import BaseModel, ConfigDict, Field


class Permission(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="The name of the permission.")
    namespace: str = Field(description="The namespace of the permission.")

    @property
    def full_name(self) -> str:
        return f"{self.namespace}.{self.name}"
