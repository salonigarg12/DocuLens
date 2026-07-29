from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.summary import Summary


def create_summary(
    db: Session,
    summary_record: Summary,
) -> Summary:
    db.add(summary_record)
    db.commit()
    db.refresh(summary_record)

    return summary_record


def get_summary_by_pdf_id(
    db: Session,
    pdf_id: str,
) -> Summary | None:
    statement = select(Summary).where(
        Summary.pdf_id == pdf_id
    )

    return db.scalar(statement)