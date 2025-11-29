import logging

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
log = logging.getLogger(__name__)


@router.get("/storage", response_model=StorageListResponse)
async def list_storage(user: AuthenticatedUser = Depends(get_current_user)):
    try:
        values = await list_storage_values(user.uid)
        return {"values": values}
    except Exception as exc:  # pragma: no cover - defensive for Cloud Run DB outages
        log.exception("Failed to list storage for user %s", user.uid)
        # Degrade gracefully so frontend can still render
        return {"values": {}}


@router.get("/storage/{key}", response_model=StorageResponse)
async def read_storage_value(key: str, user: AuthenticatedUser = Depends(get_current_user)):
    try:
        value = await get_storage_value(user.uid, key)
        if value is None:
            raise HTTPException(status_code=404, detail="Not found")
        return {"value": value}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log.exception("Failed to read storage key %s for user %s", key, user.uid)
        raise HTTPException(status_code=503, detail="Storage unavailable") from exc


@router.put("/storage/{key}", response_model=StorageResponse)
async def write_storage_value(key: str, payload: dict, user: AuthenticatedUser = Depends(get_current_user)):
    value = payload.get("value")
    try:
        saved = await set_storage_value(user.uid, key, value, user.email)
        return {"value": saved}
    except Exception as exc:  # pragma: no cover
        log.exception("Failed to write storage key %s for user %s", key, user.uid)
        raise HTTPException(status_code=503, detail="Storage unavailable") from exc


@router.delete("/storage/{key}")
async def remove_storage_value(key: str, user: AuthenticatedUser = Depends(get_current_user)):
    try:
        await delete_storage_value(user.uid, key)
        return {"ok": True}
    except Exception as exc:  # pragma: no cover
        log.exception("Failed to delete storage key %s for user %s", key, user.uid)
        raise HTTPException(status_code=503, detail="Storage unavailable") from exc
