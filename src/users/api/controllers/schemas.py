from __future__ import annotations

from pydantic import BaseModel


class OperationResultResponse(BaseModel):
    """Generic response for operations."""

    message: str
    success: bool = True
    code: int = 200
