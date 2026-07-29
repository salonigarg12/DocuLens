from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    status,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.pdf_service import upload_pdf_for_chat


router = APIRouter(
    prefix="/chats",
    tags=["PDF"],
)


class PDFUploadResponse(BaseModel):
    pdf_id: str
    chat_id: str
    pdf_name: str
    pdf_size: int
    message: str


@router.post(
    "/{chat_id}/upload",
    response_model=PDFUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_pdf(
    chat_id: str,
    file: Annotated[
        UploadFile,
        File(...),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    pdf_document = await upload_pdf_for_chat(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
        file=file,
    )

    return {
        "pdf_id": pdf_document.pdf_id,
        "chat_id": pdf_document.chat_id,
        "pdf_name": pdf_document.pdf_name,
        "pdf_size": pdf_document.pdf_size,
        "message": "PDF uploaded and indexed successfully.",
    }