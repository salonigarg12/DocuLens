import logging
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import (
    GENERATIVE_MODEL_NAME,
    MAX_CONTEXT_LENGTH,
)
from app.models.user import User
from app.repositories.pdf_repository import get_pdf_by_chat_id
import app.services.runtime as runtime
from app.services.chat_management_service import get_user_chat
from app.services.message_service import (
    save_assistant_message,
    save_user_message,
)
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.storage_service import load_chat_resources


logger = logging.getLogger(__name__)


def generate_chat_answer(
    db: Session,
    current_user: User,
    chat_id: str,
    question: str,
) -> str:
    """
    Generate an answer using the PDF connected to a chat.

    This function:
    1. Verifies that the chat belongs to the logged-in user.
    2. Finds the PDF connected to the chat.
    3. Loads its FAISS index and chunks from memory or disk.
    4. Saves the user's question in MySQL.
    5. Retrieves relevant PDF chunks.
    6. Generates an answer using Gemini.
    7. Saves the assistant's answer in MySQL.
    8. Updates the chat's last activity time.
    """

    cleaned_question = question.strip()

    if not cleaned_question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question cannot be empty.",
        )

    # Verify that the chat exists and belongs to the logged-in user.
    chat = get_user_chat(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
    )

    # Find the PDF connected to this chat.
    pdf_document = get_pdf_by_chat_id(
        db=db,
        chat_id=chat_id,
    )

    if pdf_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PDF has been uploaded for this chat.",
        )

    # Load chunks and FAISS index.
    # If they are not available in runtime memory,
    # storage_service will load them from disk.
    try:
        stored_document = load_chat_resources(
            pdf_id=pdf_document.pdf_id,
        )

    except FileNotFoundError as exc:
        logger.exception(
            "Stored PDF resources were not found for PDF %s",
            pdf_document.pdf_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "The PDF search files could not be found. "
                "Please upload the PDF again in a new chat."
            ),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Failed to load PDF resources for PDF %s",
            pdf_document.pdf_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load the PDF search resources.",
        ) from exc

    chunks = stored_document.get("chunks")
    index = stored_document.get("index")

    if not chunks or index is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The stored PDF resources are incomplete.",
        )

    # Save the user's question in the messages table.
    save_user_message(
        db=db,
        chat_id=chat_id,
        content=cleaned_question,
    )

    relevant_chunks = retrieve_relevant_chunks(
        question=cleaned_question,
        chunks=chunks,
        index=index,
    )

    if not relevant_chunks:
        answer = "I could not find this information in the document."

        save_assistant_message(
            db=db,
            chat_id=chat_id,
            content=answer,
        )

        chat.updated_at = datetime.utcnow()
        db.commit()

        return answer

    context = "\n\n".join(
        relevant_chunks
    )[:MAX_CONTEXT_LENGTH]

    prompt = f"""
You are a helpful PDF assistant.

Answer the user's question using only the provided PDF content.

Rules:
1. Do not use outside knowledge.
2. Give a clear and direct answer.
3. If the answer is not available in the provided content, say exactly:
   "I could not find this information in the document."
4. Do not make up information.

PDF Content:
{context}

Question:
{cleaned_question}
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
            "LLM request failed for chat %s",
            chat_id,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service could not generate an answer.",
        ) from exc

    answer = getattr(response, "text", None)

    if not answer or not answer.strip():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI model returned an empty response.",
        )

    answer = answer.strip()

    # Save the generated assistant response.
    save_assistant_message(
        db=db,
        chat_id=chat_id,
        content=answer,
    )

    # Move this chat to the top of the recent-chat list.
    chat.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(chat)

    return answer