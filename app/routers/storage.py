from fastapi import APIRouter, Depends, HTTPException

from ..core.auth import get_current_user
from ..models.storage import StorageListResponse, StorageResponse
from ..models.user import AuthenticatedUser
from ..services.storage_service import (
    delete_storage_value,
    get_storage_value,
    list_storage_values,
    set_storage_value,
)

router = APIRouter()


@router.get("/storage", response_model=StorageListResponse)
async def list_storage(user: AuthenticatedUser = Depends(get_current_user)):
    values = await list_storage_values(user.uid)
    return {"values": values}


@router.get("/storage/{key}", response_model=StorageResponse)
async def read_storage_value(key: str, user: AuthenticatedUser = Depends(get_current_user)):
    value = await get_storage_value(user.uid, key)
    if value is None:
        raise HTTPException(status_code=404, detail="Not found")
    return {"value": value}


@router.put("/storage/{key}", response_model=StorageResponse)
async def write_storage_value(key: str, payload: dict, user: AuthenticatedUser = Depends(get_current_user)):
    value = payload.get("value")
    saved = await set_storage_value(user.uid, key, value, user.email)
    return {"value": saved}


@router.delete("/storage/{key}")
async def remove_storage_value(key: str, user: AuthenticatedUser = Depends(get_current_user)):
    await delete_storage_value(user.uid, key)
    return {"ok": True}
