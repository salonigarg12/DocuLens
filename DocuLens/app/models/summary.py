from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Summary(Base):
    __tablename__ = "summaries"

    summary_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    pdf_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "pdf_documents.pdf_id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
        index=True,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )