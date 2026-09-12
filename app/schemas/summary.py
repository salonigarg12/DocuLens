from datetime import datetime

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    summary_id: str
    pdf_id: str
    summary: str
    generated_at: datetime

    model_config = {
        "from_attributes": True
    }