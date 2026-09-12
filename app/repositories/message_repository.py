from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message


def create_message(
    db: Session,
    message: Message,
) -> Message:
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_messages_by_chat(
    db: Session,
    chat_id: str,
) -> list[Message]:
    statement = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.sent_at.asc())
    )

    return list(db.scalars(statement).all())