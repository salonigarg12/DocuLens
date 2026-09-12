import logging
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import (
    GENERATIVE_MODEL_NAME,
    MAX_SUMMARY_LENGTH,
    SUMMARY_CHUNKS,
)
from app.models.summary import Summary
from app.models.user import User
from app.repositories.pdf_repository import get_pdf_by_chat_id
from app.repositories.summary_repository import (
    create_summary,
    get_summary_by_pdf_id,
)
import app.services.runtime as runtime
from app.services.chat_management_service import get_user_chat
from app.services.message_service import save_assistant_message
from app.services.storage_service import load_chat_resources


logger = logging.getLogger(__name__)


def generate_chat_summary(
    db: Session,
    current_user: User,
    chat_id: str,
) -> Summary:
    """
    Return the saved summary if one already exists.

    Otherwise:
    1. Verify chat ownership.
    2. Find the PDF connected to the chat.
    3. Load PDF chunks from memory or disk.
    4. Generate a summary using Gemini.
    5. Save the summary in MySQL.
    6. Save the summary as an assistant message.
    7. Update the chat activity time.
    """

    chat = get_user_chat(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
    )

    pdf_document = get_pdf_by_chat_id(
        db=db,
        chat_id=chat_id,
    )

    if pdf_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PDF has been uploaded for this chat.",
        )

    existing_summary = get_summary_by_pdf_id(
        db=db,
        pdf_id=pdf_document.pdf_id,
    )

    if existing_summary is not None:
        return existing_summary

    try:
        stored_document = load_chat_resources(
            pdf_id=pdf_document.pdf_id,
        )

    except FileNotFoundError as exc:
        logger.exception(
            "Stored resources not found for PDF %s",
            pdf_document.pdf_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "The PDF processing files could not be found. "
                "Please upload the PDF again in a new chat."
            ),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Failed to load resources for PDF %s",
            pdf_document.pdf_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load the PDF resources.",
        ) from exc

    chunks = stored_document.get("chunks")

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No PDF chunks are available for summarization.",
        )

    selected_chunks = chunks[:SUMMARY_CHUNKS]

    summary_context = "\n\n".join(
        selected_chunks
    )[:MAX_SUMMARY_LENGTH]

    prompt = f"""
You are a helpful PDF summarization assistant.

Create a clear and well-structured summary using only the provided PDF content.

Instructions:
1. Do not use outside knowledge.
2. Include the main ideas and important details.
3. Use simple and understandable language.
4. Avoid unnecessary repetition.
5. Organize the summary into short paragraphs or bullet points where helpful.
6. Do not mention that only selected chunks were provided.
7. Do not invent information.

PDF Content:
{summary_context}
""".strip()

    if runtime.google_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google GenAI client has not been initialized.",
        )

    try:
        response = runtime.google_client.models.generate_content(
            model=GENERATIVE_MODEL_NAME,
            contents=prompt,
        )

    except Exception as exc:
        logger.exception(
            "Summary generation failed for chat %s",
            chat_id,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service could not generate the summary.",
        ) from exc

    summary_text = getattr(response, "text", None)

    if not summary_text or not summary_text.strip():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI model returned an empty summary.",
        )

    summary_text = summary_text.strip()

    summary_record = Summary(
        summary_id=str(uuid.uuid4()),
        pdf_id=pdf_document.pdf_id,
        summary=summary_text,
    )

    try:
        saved_summary = create_summary(
            db=db,
            summary_record=summary_record,
        )

        save_assistant_message(
            db=db,
            chat_id=chat_id,
            content=summary_text,
        )

        chat.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(chat)

        return saved_summary

    except Exception as exc:
        db.rollback()

        logger.exception(
            "Failed to save summary for chat %s",
            chat_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The summary was generated but could not be saved.",
        ) from exc