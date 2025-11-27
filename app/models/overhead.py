from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict


class OverheadEmployee(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = None
    user_id: Optional[str] = None
    department: str
    employee_name: str
    role: str
    location: Optional[str] = None
    annual_salary: float
    allocation_percent: float
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    monthly_allocations: Dict[str, float]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
