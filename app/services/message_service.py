import uuid

from sqlalchemy.orm import Session

from app.models.message import Message, MessageSender
from app.repositories.message_repository import (
    create_message,
    get_messages_by_chat,
)


def save_user_message(
    db: Session,
    chat_id: str,
    content: str,
):
    message = Message(
        message_id=str(uuid.uuid4()),
        chat_id=chat_id,
        content=content,
        sent_by=MessageSender.USER,
    )

    return create_message(db, message)


def save_assistant_message(
    db: Session,
    chat_id: str,
    content: str,
):
    message = Message(
        message_id=str(uuid.uuid4()),
        chat_id=chat_id,
        content=content,
        sent_by=MessageSender.ASSISTANT,
    )

    return create_message(db, message)


def load_chat_messages(
    db: Session,
    chat_id: str,
):
    return get_messages_by_chat(db, chat_id)