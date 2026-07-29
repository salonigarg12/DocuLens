from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session


from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatCreate,
    ChatRename,
    ChatResponse,
)
from app.services.chat_management_service import (
    create_user_chat,
    delete_user_chat,
    get_user_chat,
    list_user_chats,
    rename_user_chat,
)


router = APIRouter(
    prefix="/chats",
    tags=["Chats"],
)


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_chat(
    chat_data: ChatCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    return create_user_chat(
        db=db,
        current_user=current_user,
        chat_data=chat_data,
    )


@router.get(
    "",
    response_model=list[ChatResponse],
)
def get_user_chats(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    return list_user_chats(
        db=db,
        current_user=current_user,
    )

@router.get(
    "/{chat_id}",
    response_model=ChatResponse,
)
def get_chat(
    chat_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    return get_user_chat(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
    )

@router.patch(
    "/{chat_id}",
    response_model=ChatResponse,
)
def rename_chat(
    chat_id: str,
    rename_data: ChatRename,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    return rename_user_chat(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
        rename_data=rename_data,
    )


@router.delete(
    "/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_chat(
    chat_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    delete_user_chat(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
    )