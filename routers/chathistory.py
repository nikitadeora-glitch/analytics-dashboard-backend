from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

router = APIRouter()


def _get_history(db: Session, session_id: str):
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.created_at.asc(), models.ChatMessage.id.asc())
        .all()
    )


@router.post("/", response_model=schemas.ChatHistoryResponse)
def create_chat_message(payload: schemas.ChatMessageCreate, db: Session = Depends(get_db)):
    role = (payload.role or "").strip().lower()
    if role not in {"user", "ai"}:
        raise HTTPException(status_code=400, detail="role must be 'user' or 'ai'")

    msg = models.ChatMessage(
        session_id=payload.session_id,
        role=role,
        message=payload.message,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    messages = _get_history(db, payload.session_id)
    return {"session_id": payload.session_id, "messages": messages}


@router.get("/{session_id}", response_model=schemas.ChatHistoryResponse)
def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    messages = _get_history(db, session_id)
    return {"session_id": session_id, "messages": messages}
