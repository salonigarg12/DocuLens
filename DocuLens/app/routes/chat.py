from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.chat_service import generate_chat_answer


router = APIRouter(
    prefix="/chats",
    tags=["Chat"],
)


class ChatQuestionRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=5000,
    )


class ChatAnswerResponse(BaseModel):
    chat_id: str
    question: str
    answer: str


@router.post(
    "/{chat_id}/ask",
    response_model=ChatAnswerResponse,
)
def ask_question(
    chat_id: str,
    request: ChatQuestionRequest,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    answer = generate_chat_answer(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
        question=request.question,
    )

    return ChatAnswerResponse(
        chat_id=chat_id,
        question=request.question,
        answer=answer,
    )