from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PDFDocument(Base):
    __tablename__ = "pdf_documents"

    pdf_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    chat_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "chats.chat_id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
        index=True,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    pdf_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    pdf_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )