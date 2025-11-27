from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PipelineEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    projectCode: Optional[str] = None
    owner: str
    client: str
    programName: str
    programType: Optional[str] = None
    region: Optional[str] = None
    startMonth: Optional[str] = None
    endMonth: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    revenue: float = 0
    totalFees: float = 0
    status: str = "open"
    accounts: float = 0
    creative: float = 0
    design: float = 0
    strategy: float = 0
    media: float = 0
    studio: float = 0
    creator: float = 0
    social: float = 0
    omni: float = 0
    finance: float = 0
    createdBy: Optional[str] = None
    updatedBy: Optional[str] = None
    createdByEmail: Optional[str] = None
    updatedByEmail: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class PipelineChange(BaseModel):
    type: str
    projectCode: str
    projectName: Optional[str] = None
    client: Optional[str] = None
    description: str
    date: str
    user: str


class PipelineResponse(BaseModel):
    entries: List[PipelineEntry]
    changelog: List[PipelineChange]
