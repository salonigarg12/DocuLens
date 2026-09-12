from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.message import MessageResponse
from app.services.chat_management_service import get_user_chat
from app.services.message_service import load_chat_messages


router = APIRouter(
    prefix="/chats",
    tags=["Messages"],
)


@router.get(
    "/{chat_id}/messages",
    response_model=list[MessageResponse],
)
def get_chat_messages(
    chat_id: str,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    get_user_chat(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
    )

    return load_chat_messages(
        db=db,
        chat_id=chat_id,
    )