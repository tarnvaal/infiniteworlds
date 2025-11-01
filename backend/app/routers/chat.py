from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import get_chatter, reset_chatter


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


class ClearRequest(BaseModel):
    clear: bool


class ClearResponse(BaseModel):
    success: bool


@router.post("/clear", response_model=ClearResponse)
def clear_chat(req: ClearRequest):
    if req.clear:
        reset_chatter()
        return ClearResponse(success=True)
    else:
        return ClearResponse(success=False)


@router.post("", response_model=ChatResponse)
def post_chat(req: ChatRequest, chatter=Depends(get_chatter)):
    try:
        reply = chatter.chat(req.message)
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)},
        )
