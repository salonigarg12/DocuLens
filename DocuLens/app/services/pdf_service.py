import io
import json
import re
import uuid
from datetime import datetime
from pathlib import Path

import faiss
import numpy as np
import pdfplumber
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

import app.services.runtime as runtime
from app.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHUNKS_DIR,
    INDEXES_DIR,
    MAX_FILE_SIZE,
    UPLOAD_DIR,
)
from app.models.pdf import PDFDocument
from app.models.user import User
from app.repositories.pdf_repository import (
    create_pdf_document,
    get_pdf_by_chat_id,
)
from app.services.chat_management_service import get_user_chat


def sanitize_filename(filename: str) -> str:
    filename = Path(filename).name

    safe_name = re.sub(
        r"[^a-zA-Z0-9._-]",
        "_",
        filename,
    )

    return safe_name or "document.pdf"


def validate_pdf(
    filename: str | None,
    contents: bytes,
) -> None:
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF filename is missing.",
        )

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed.",
        )

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF is empty.",
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="PDF size must not exceed 10 MB.",
        )

    if not contents.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid PDF.",
        )


def extract_pdf_text(contents: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            pages: list[str] = []

            for page in pdf.pages:
                page_text = page.extract_text()

                if page_text:
                    pages.append(page_text)

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read the PDF.",
        ) from error

    text = "\n\n".join(pages).strip()

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No readable text was found in the PDF. "
                "Scanned PDFs are currently not supported."
            ),
        )

    return text


def chunk_text(text: str) -> list[str]:
    chunks: list[str] = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(
            start + CHUNK_SIZE,
            text_length,
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == text_length:
            break

        start = end - CHUNK_OVERLAP

    return chunks


def create_faiss_index(
    chunks: list[str],
):
    if runtime.embedding_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding model is not available.",
        )

    embeddings = runtime.embedding_model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32",
    )

    if embeddings.ndim != 2 or embeddings.shape[0] == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create embeddings for the PDF.",
        )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index


def save_pdf_file(
    pdf_id: str,
    filename: str,
    contents: bytes,
) -> Path:
    safe_filename = sanitize_filename(filename)

    stored_filename = f"{pdf_id}_{safe_filename}"
    file_path = UPLOAD_DIR / stored_filename

    try:
        file_path.write_bytes(contents)

    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the uploaded PDF.",
        ) from error

    return file_path


def save_chunks(
    pdf_id: str,
    chunks: list[str],
) -> Path:
    chunks_path = CHUNKS_DIR / f"{pdf_id}.json"

    try:
        with chunks_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                chunks,
                file,
                ensure_ascii=False,
                indent=2,
            )

    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the PDF chunks.",
        ) from error

    return chunks_path


def save_faiss_index(
    pdf_id: str,
    index,
) -> Path:
    index_path = INDEXES_DIR / f"{pdf_id}.faiss"

    try:
        faiss.write_index(
            index,
            str(index_path),
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the search index.",
        ) from error

    return index_path


def remove_created_files(
    paths: list[Path],
) -> None:
    for path in paths:
        try:
            if path.exists() and path.is_file():
                path.unlink()

        except OSError:
            pass


async def upload_pdf_for_chat(
    db: Session,
    current_user: User,
    chat_id: str,
    file: UploadFile,
) -> PDFDocument:
    chat = get_user_chat(
        db=db,
        current_user=current_user,
        chat_id=chat_id,
    )

    existing_pdf = get_pdf_by_chat_id(
        db=db,
        chat_id=chat_id,
    )

    if existing_pdf is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This chat already has a PDF.",
        )

    contents = await file.read()

    validate_pdf(
        filename=file.filename,
        contents=contents,
    )

    text = extract_pdf_text(contents)
    chunks = chunk_text(text)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No text chunks could be created.",
        )

    index = create_faiss_index(chunks)

    pdf_id = str(uuid.uuid4())
    created_files: list[Path] = []

    try:
        file_path = save_pdf_file(
            pdf_id=pdf_id,
            filename=file.filename or "document.pdf",
            contents=contents,
        )
        created_files.append(file_path)

        chunks_path = save_chunks(
            pdf_id=pdf_id,
            chunks=chunks,
        )
        created_files.append(chunks_path)

        index_path = save_faiss_index(
            pdf_id=pdf_id,
            index=index,
        )
        created_files.append(index_path)

        pdf_document = PDFDocument(
            pdf_id=pdf_id,
            chat_id=chat_id,
            file_path=str(file_path),
            pdf_name=file.filename or "document.pdf",
            pdf_size=len(contents),
        )

        saved_pdf = create_pdf_document(
            db=db,
            pdf_document=pdf_document,
        )

        chat.chat_name = file.filename or chat.chat_name
        chat.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(chat)

        runtime.documents[pdf_id] = {
            "pdf_id": pdf_id,
            "chunks": chunks,
            "index": index,
        }

        return saved_pdf

    except HTTPException:
        db.rollback()
        remove_created_files(created_files)
        runtime.documents.pop(pdf_id, None)
        raise

    except Exception as error:
        db.rollback()
        remove_created_files(created_files)
        runtime.documents.pop(pdf_id, None)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF processing failed.",
        ) from error

    finally:
        await file.close()