from pydantic import BaseModel, ConfigDict, Field


class TokenPairInput(BaseModel):
    email: str = Field(..., description="User email", examples=["admin@app.com"])
    password: str = Field(..., description="User password", examples=["Admin@123"])


class TokenConfigurations(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ALGORITHM: str
    SECRET_KEY: str
    REFRESH_TOKEN_TTL_DAYS: int
    ACCESS_TOKEN_TTL_SECONDS: int
