from fastapi import WebSocket, Depends, APIRouter
from sqlalchemy.orm import Session
from database import get_db
import model
import schema
from datetime import datetime

router = APIRouter(
    prefix='/websocket',
    tags=['websocket']
)



@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    await websocket.accept()
    # Verify user is a participant
    chat = db.query(model.Chat).filter(model.Chat.id == chat_id).first()
    if not chat or current_user not in chat.participants:
        await websocket.close(code=1008)
        return
    while True:
        data = await websocket.receive_json()
        message = model.Message(
            sender_id=current_user.id,
            receiver_id=data["receiver_id"],
            chat_id=chat_id,
            content=data["content"],
            message_type=data.get("message_type", schema.MessageType.TEXT),
            timestamp=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        await websocket.send_json({"message": "Message sent", "content": data["content"]})