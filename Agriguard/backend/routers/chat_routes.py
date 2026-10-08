import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import User, Report, Conversation, Message
from backend.schemas import ChatRequest, ChatResponse, ConversationResponse, ChatMessage
from backend.auth import get_current_user
from backend.services.chatbot import bot_engine

logger = logging.getLogger("agriguard.chat")

router = APIRouter(tags=["AgriBot Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(
    chat_req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a message to AgriBot.
    Grounded on report disease context if report_id is passed, or provides general agricultural guidance.
    """
    report = None
    insight = None
    severity = "Medium"

    # 1. Resolve Report Context
    if chat_req.report_id:
        report = db.query(Report).filter(Report.id == chat_req.report_id).first()
        if report:
            if current_user.role != "expert" and report.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to access this report's chat.")
            if report.insight_json:
                try:
                    insight = json.loads(report.insight_json)
                except Exception:
                    pass
            severity = report.severity or "Medium"

    # 2. Resolve Conversation
    conversation = None
    if chat_req.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == chat_req.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    elif chat_req.report_id:
        # Check if conversation already exists for this report
        conversation = db.query(Conversation).filter(
            Conversation.report_id == chat_req.report_id,
            Conversation.user_id == current_user.id
        ).first()

    if not conversation:
        title = f"Chat: {report.crop} ({report.predicted_class})" if report else "AgriBot Advisory Chat"
        conversation = Conversation(
            user_id=current_user.id,
            report_id=chat_req.report_id,
            title=title
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 3. Retrieve recent history for conversational continuity
    recent_db_msgs = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(desc(Message.id)).limit(20).all()
    # Reverse so it's chronological
    recent_history = [
        {"role": m.role, "content": m.content}
        for m in reversed(recent_db_msgs)
    ]

    # 4. Save user message
    user_msg_record = Message(
        conversation_id=conversation.id,
        role="user",
        content=chat_req.message.strip()
    )
    db.add(user_msg_record)
    db.commit()

    # 5. Generate AgriBot reply
    reply_text, detected_intent, chips = await bot_engine.get_reply(
        user_message=chat_req.message,
        insight=insight,
        severity=severity,
        recent_history=recent_history
    )

    # 6. Save assistant reply
    asst_msg_record = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text
    )
    db.add(asst_msg_record)
    db.commit()

    lang = bot_engine.detect_language(chat_req.message)

    return ChatResponse(
        conversation_id=conversation.id,
        reply=reply_text,
        detected_intent=detected_intent,
        language=lang,
        quick_chips=chips
    )


@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all chat conversations for the current user."""
    convs = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(desc(Conversation.created_at)).all()
    return convs


@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessage])
def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all message history for a specific conversation."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    msgs = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.id.asc()).all()
    return msgs


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a conversation and its messages."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    db.delete(conv)
    db.commit()
    return None
