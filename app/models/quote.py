from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class QuotePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    projectNumber: Optional[str] = None
    clientName: Optional[str] = None
    projectName: Optional[str] = None
    status: Optional[str] = None
    full_quote: Optional[Dict[str, Any]] = None


class QuotesReplaceRequest(BaseModel):
    quotes: List[QuotePayload]


class QuotesResponse(BaseModel):
    quotes: List[Dict[str, Any]]
