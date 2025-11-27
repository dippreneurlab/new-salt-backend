from typing import Dict, List
from pydantic import BaseModel


class PipelineMetadataResponse(BaseModel):
    clients: List[str]
    rateCardMap: Dict[str, str]
    clientCategoryMap: Dict[str, str]
