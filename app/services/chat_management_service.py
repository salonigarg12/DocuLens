import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import CHUNKS_DIR, INDEXES_DIR
from app.models.chat import Chat
from app.models.user import User
from app.repositories.chat_repository import (
    create_chat,
    get_chat_by_id,
    get_chats_by_username,
    soft_delete_chat,
    update_chat,
)
from app.repositories.pdf_repository import get_pdf_by_chat_id
from app.schemas.chat import ChatCreate, ChatRename
import app.services.runtime as runtime


logger = logging.getLogger(__name__)


def create_user_chat(
    db: Session,
    current_user: User,
    chat_data: ChatCreate,
) -> Chat:
    cleaned_chat_name = chat_data.chat_name.strip()

    if not cleaned_chat_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chat name cannot be empty.",
        )

    chat = Chat(
        chat_id=str(uuid.uuid4()),
        username=current_user.username,
        chat_name=cleaned_chat_name,
    )

    return create_chat(
        db=db,
        chat=chat,
    )


def list_user_chats(
    db: Session,
    current_user: User,
) -> list[Chat]:
    return get_chats_by_username(
        db=db,
        username=current_user.username,
    )


def get_user_chat(
    db: Session,
    current_user: User,
    chat_id: str,
) -> Chat:
    chat = get_chat_by_id(
        db=db,
        chat_id=chat_id,
    )

    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found.",
        )

    if chat.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found.",
        )

    return chat


def rename_user_chat(
    db: Session,
    current_user: User,
    chat_id: str,
    rename_data: ChatRename,
) -> Chat:
    chat = get_user_chat(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
    )

    cleaned_chat_name = rename_data.chat_name.strip()

    if not cleaned_chat_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chat name cannot be empty.",
        )

    chat.chat_name = cleaned_chat_name
    chat.updated_at = datetime.utcnow()

    return update_chat(
        db=db,
        chat=chat,
    )


def delete_file_safely(
    file_path: str | Path | None,
) -> None:
    if not file_path:
        return

    try:
        path = Path(file_path)

        if path.exists() and path.is_file():
            path.unlink()

    except OSError:
        logger.exception(
            "Could not delete file: %s",
            file_path,
        )


def delete_pdf_resources(
    pdf_id: str,
    uploaded_pdf_path: str | None,
) -> None:
    runtime.documents.pop(pdf_id, None)

    delete_file_safely(uploaded_pdf_path)
    delete_file_safely(CHUNKS_DIR / f"{pdf_id}.json")
    delete_file_safely(INDEXES_DIR / f"{pdf_id}.faiss")


def delete_user_chat(
    db: Session,
    current_user: User,
    chat_id: str,
) -> None:
    chat = get_user_chat(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
    )

    pdf_document = get_pdf_by_chat_id(
        db=db,
        chat_id=chat_id,
    )

    if pdf_document is not None:
        delete_pdf_resources(
            pdf_id=pdf_document.pdf_id,
            uploaded_pdf_path=pdf_document.file_path,
        )

    soft_delete_chat(
        db=db,
        chat=chat,
    )