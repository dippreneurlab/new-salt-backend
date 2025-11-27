from fastapi import APIRouter, Body, Depends, HTTPException

from ..core.auth import require_admin
from ..models.user import AuthenticatedUser
from ..services.roles_service import set_user_role

router = APIRouter()


@router.post("/setRole")
async def set_role(
    payload: dict = Body(...),
    admin_user: AuthenticatedUser = Depends(require_admin),
):
    uid = payload.get("uid") if isinstance(payload, dict) else None
    role = payload.get("role") if isinstance(payload, dict) else None
    if not uid or not role:
        raise HTTPException(status_code=400, detail="uid and role are required")
    await set_user_role(uid, role)
    return {"ok": True, "uid": uid, "role": role}
