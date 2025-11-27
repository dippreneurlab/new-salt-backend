from fastapi import APIRouter, Body, Depends, HTTPException

from ..core.auth import get_current_user
from ..models.quote import QuotesReplaceRequest, QuotesResponse
from ..models.user import AuthenticatedUser
from ..services.quotes_service import get_quotes_for_user, replace_quotes

router = APIRouter()


@router.get("/quotes", response_model=QuotesResponse)
async def list_quotes(user: AuthenticatedUser = Depends(get_current_user)):
    quotes = await get_quotes_for_user(user.uid)
    return {"quotes": quotes}


@router.post("/quotes", response_model=QuotesResponse)
async def replace_quotes_bulk(
    payload: QuotesReplaceRequest = Body(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    if not payload.quotes:
        raise HTTPException(status_code=400, detail="quotes array is required")
    await replace_quotes(user.uid, payload.quotes, user.email)
    quotes = await get_quotes_for_user(user.uid)
    return {"quotes": quotes}
