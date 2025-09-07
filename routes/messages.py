from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from . auth import get_current_user
import schema
import model
from datetime import datetime






router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=schema.MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message: schema.MessageCreate,
    db: Session = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot send message as another user")
    receiver = db.query(model.User).filter(model.User.id == message.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receiver not found")
    db_message = model.Message(
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        content=message.content,
        message_type=message.message_type,
        attachment_url=message.attachment_url,
        parent_message_id=message.parent_message_id,
        timestamp=datetime.utcnow(),
        is_read=message.is_read
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message