from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import Chat


def create_chat(
    db: Session,
    chat: Chat,
) -> Chat:
    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat


def get_chats_by_username(
    db: Session,
    username: str,
) -> list[Chat]:
    statement = (
        select(Chat)
        .where(
            Chat.username == username,
            Chat.is_deleted.is_(False),
        )
        .order_by(Chat.updated_at.desc())
    )

    return list(db.scalars(statement).all())


def get_chat_by_id(
    db: Session,
    chat_id: str,
) -> Chat | None:
    statement = select(Chat).where(
        Chat.chat_id == chat_id,
        Chat.is_deleted.is_(False),
    )

    return db.scalar(statement)


def update_chat(
    db: Session,
    chat: Chat,
) -> Chat:
    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat


def soft_delete_chat(
    db: Session,
    chat: Chat,
) -> Chat:
    chat.is_deleted = True

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat