# Chat router handling Granite LLM interactions backed by persistent storage.
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, cast

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models import ChatMessage, User
from app.services.granite_llm import granite_llm

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatMessageRecord(BaseModel):
    sender: str
    message: str
    timestamp: datetime


class ChatResponse(BaseModel):
    response: str
    status: str
    history: List[ChatMessageRecord]


def _chat_to_dict(entry: ChatMessage) -> ChatMessageRecord:
    obj = cast(Any, entry)
    return ChatMessageRecord(
        sender=obj.sender,
        message=obj.message,
        timestamp=obj.created_at,
    )


def _get_recent_history(db: Session, user_id: int, limit: int = 50) -> List[ChatMessageRecord]:
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed([_chat_to_dict(row) for row in rows]))


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Handle chat queries using Granite LLM and persist the full conversation."""

    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    try:
        db.add(ChatMessage(user_id=int(cast(Any, current_user).id), sender="user", message=message))
        db.commit()
    except Exception as exc:  # pragma: no cover
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to log chat message: {exc}")

    try:
        response_text = granite_llm.ask_granite(message)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Assistant error: {exc}")

    try:
        db.add(ChatMessage(user_id=int(cast(Any, current_user).id), sender="assistant", message=response_text))
        db.commit()
    except Exception as exc:  # pragma: no cover
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to persist assistant reply: {exc}")

    user_obj = cast(Any, current_user)
    history = _get_recent_history(db, int(user_obj.id))

    return ChatResponse(response=response_text, status="success", history=history)


@router.get("/history", response_model=Dict[str, Any])
async def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return saved chat history for the authenticated user."""

    user_obj = cast(Any, current_user)
    history = _get_recent_history(db, int(user_obj.id), limit=100)
    return {"history": [message.model_dump() for message in history], "count": len(history), "status": "success"}


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete all chat history for the authenticated user."""

    user_obj = cast(Any, current_user)
    user_id = int(user_obj.id)

    try:
        db.query(ChatMessage).filter(ChatMessage.user_id == user_id).delete(synchronize_session=False)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete history: {exc}")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
