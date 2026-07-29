from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.summary import SummaryResponse
from app.services.summary_service import generate_chat_summary


router = APIRouter(
    prefix="/chats",
    tags=["Summary"],
)


@router.post(
    "/{chat_id}/summary",
    response_model=SummaryResponse,
)
def summarize_chat_pdf(
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
    return generate_chat_summary(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
    )