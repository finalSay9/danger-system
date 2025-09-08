# chats.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
import schema
import model

router = APIRouter(prefix="/chats", tags=["chats"])

@router.get("/", response_model=list[schema.Chat])
async def get_chats(current_user: model.User = Depends(get_current_user), db: Session = Depends(get_db)):
  chats = db.query(model.Chat).filter(model.Chat.participants.any(id=current_user.id)).all()
  return chats