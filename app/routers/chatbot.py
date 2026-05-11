import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..chatbot_data import reply_for

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])


@router.get("/history")
def chat_history(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    msgs = db.query(models.ChatMessage).filter_by(user_id=user.id).order_by(models.ChatMessage.created_at).limit(100).all()
    return [{"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in msgs]


@router.post("/stream")
async def chat_stream(payload: schemas.ChatIn, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Save user message
    db.add(models.ChatMessage(user_id=user.id, role="user", content=payload.message))
    db.commit()

    response_text = reply_for(payload.message)

    # Persist bot reply
    db.add(models.ChatMessage(user_id=user.id, role="bot", content=response_text))
    db.commit()

    async def streamer():
        # Stream word by word with small delay to feel like typing
        words = response_text.split(" ")
        for i, w in enumerate(words):
            chunk = (" " if i > 0 else "") + w
            yield chunk
            await asyncio.sleep(0.04)

    return StreamingResponse(streamer(), media_type="text/plain")
