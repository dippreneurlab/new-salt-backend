from fastapi import APIRouter, Body, Depends, HTTPException

from ..core.auth import get_current_user
from ..models.overhead import OverheadEmployee
from ..models.user import AuthenticatedUser
from ..services.overhead_service import delete_overhead_employee, list_overhead_employees, upsert_overhead_employees

router = APIRouter()


@router.get("/overhead-employees")
async def get_overhead_employees(user: AuthenticatedUser = Depends(get_current_user)):
    employees = await list_overhead_employees(user.uid)
    return {"employees": employees}


@router.post("/overhead-employees")
async def save_overhead_employees(
    payload: dict = Body(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    employees_data = payload.get("employees") if isinstance(payload, dict) else None
    if employees_data is None:
        raise HTTPException(status_code=400, detail="employees is required")
    employees = [OverheadEmployee.model_validate(emp) for emp in employees_data]
    saved = await upsert_overhead_employees(user.uid, employees, user.email or user.uid)
    return {"employees": saved}


@router.delete("/overhead-employees")
async def remove_overhead_employee(
    payload: dict = Body(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    emp_id = payload.get("id") if isinstance(payload, dict) else None
    if not emp_id:
        raise HTTPException(status_code=400, detail="id is required")
    await delete_overhead_employee(user.uid, emp_id)
    return {"ok": True}
