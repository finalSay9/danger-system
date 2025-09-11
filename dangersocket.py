from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from database import get_db
import model, schema
from routes.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix='/websocket', tags=['websocket'])

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    # Accept the connection
    await websocket.accept()

    # Verify user from token
    current_user = await get_current_user(token, db)
    if not current_user:
        await websocket.close(code=1008)
        return

    chat_id = int(websocket.query_params.get("chat_id"))
    chat = db.query(model.Chat).filter(model.Chat.id == chat_id).first()
    if not chat:
        await websocket.close(code=1008)
        return

    try:
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
    except WebSocketDisconnect:
        print(f"User {current_user.email} disconnected")
