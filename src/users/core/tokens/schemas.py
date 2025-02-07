from pydantic import BaseModel, Field


class TokenPairInput(BaseModel):
    email: str = Field(..., description="User email", examples=["admin@app.com"])
    password: str = Field(..., description="User password", examples=["Admin@123"])
