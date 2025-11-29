from fastapi import APIRouter, Body, Depends, HTTPException

from ..core.auth import get_current_user
from ..models.pipeline import PipelineEntry, PipelineResponse
from ..models.user import AuthenticatedUser
from ..services.pipeline_service import (
    build_pipeline_changelog,
    create_pipeline_entry as create_pipeline_entry_service,
    delete_pipeline_entry,
    get_next_project_code,
    get_pipeline_entries_for_user,
    update_existing_pipeline_entry,
)

router = APIRouter()


@router.get("/pipeline", response_model=PipelineResponse)
async def list_pipeline(user: AuthenticatedUser = Depends(get_current_user)):
    entries = await get_pipeline_entries_for_user(user.uid)
    changelog = build_pipeline_changelog(entries, user.email or user.uid)
    return {"entries": entries, "changelog": changelog}


@router.post("/pipeline", response_model=PipelineEntry)
async def create_pipeline_entry(payload: dict = Body(...), user: AuthenticatedUser = Depends(get_current_user)):
    entry_data = payload.get("entry") if isinstance(payload, dict) else None
    entry_data = entry_data or payload
    if not entry_data:
        raise HTTPException(status_code=400, detail="entry is required")

    entry = PipelineEntry.model_validate(entry_data)

    saved = await create_pipeline_entry_service(user.uid, entry, user.email)
    return saved


@router.put("/pipeline", response_model=PipelineEntry)
async def update_pipeline_entry(payload: dict = Body(...), user: AuthenticatedUser = Depends(get_current_user)):
    entry_data = payload.get("entry") if isinstance(payload, dict) else None
    entry_data = entry_data or payload
    if not entry_data:
        raise HTTPException(status_code=400, detail="entry is required")

    entry = PipelineEntry.model_validate(entry_data)
    if not entry.projectCode:
        raise HTTPException(status_code=400, detail="projectCode is required")

    try:
        saved = await update_existing_pipeline_entry(user.uid, entry, user.email)
        return saved
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/pipeline")
async def remove_pipeline_entry(payload: dict = Body(...), user: AuthenticatedUser = Depends(get_current_user)):
    project_code = payload.get("projectCode") if isinstance(payload, dict) else None
    if not project_code:
        raise HTTPException(status_code=400, detail="projectCode is required")
    await delete_pipeline_entry(project_code, user.uid, user.email)
    return {"ok": True}


@router.get("/pipeline/next-code")
async def next_project_code(year: str):
    return {"projectCode": await get_next_project_code(year)}
