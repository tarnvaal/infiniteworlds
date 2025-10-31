from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..dependencies import get_chatter


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
def post_chat(req: ChatRequest, chatter=Depends(get_chatter)):
    reply = chatter.chat(req.message)
    return ChatResponse(reply=reply)
