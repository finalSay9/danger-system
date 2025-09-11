# chats.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . auth import get_current_user
from database import get_db
import schema
import model
from datetime import datetime

router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("/", response_model=schema.ChatResponse)
async def create_chat(chat: schema.ChatCreate, current_user: model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not chat.participant_ids or current_user.id not in chat.participant_ids:
        raise HTTPException(status_code=400, detail="Invalid participant IDs")
    
    db_chat = model.Chat(name=chat.name, created_at=datetime.utcnow())
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    
    for user_id in chat.participant_ids:
        user = db.query(model.User).filter(model.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        db.execute(
            model.chat_participants.insert().values(chat_id=db_chat.id, user_id=user_id)
        )
    db.commit()
    db_chat.participants = (
        db.query(model.User)
        .filter(model.User.id.in_(chat.participant_ids))
        .all()
    )
    return db_chat

@router.get("/", response_model=list[schema.ChatResponse])
async def get_chats(current_user: model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = (
        db.query(model.Chat)
        .join(model.chat_participants)
        .filter(model.chat_participants.c.user_id == current_user.id)
        .all()
    )
    return chats