from typing import Any, Dict, Optional
from pydantic import BaseModel


class StorageItem(BaseModel):
    key: str
    value: Optional[Any] = None


class StorageResponse(BaseModel):
    value: Optional[Any] = None


class StorageListResponse(BaseModel):
    values: Dict[str, Any]
