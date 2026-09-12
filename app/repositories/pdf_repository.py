from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pdf import PDFDocument


def create_pdf_document(
    db: Session,
    pdf_document: PDFDocument,
) -> PDFDocument:
    db.add(pdf_document)
    db.commit()
    db.refresh(pdf_document)

    return pdf_document


def get_pdf_by_chat_id(
    db: Session,
    chat_id: str,
) -> PDFDocument | None:
    statement = select(PDFDocument).where(
        PDFDocument.chat_id == chat_id
    )

    return db.scalar(statement)


def get_pdf_by_id(
    db: Session,
    pdf_id: str,
) -> PDFDocument | None:
    statement = select(PDFDocument).where(
        PDFDocument.pdf_id == pdf_id
    )

    return db.scalar(statement)