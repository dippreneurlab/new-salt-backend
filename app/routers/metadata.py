from fastapi import APIRouter

from ..models.metadata import PipelineMetadataResponse
from ..services.metadata_service import get_pipeline_metadata

router = APIRouter()


@router.get("/metadata/pipeline", response_model=PipelineMetadataResponse)
async def pipeline_metadata():
    return get_pipeline_metadata()
