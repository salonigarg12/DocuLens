from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message_id: str
    content: str
    sent_by: str
    sent_at: datetime

    model_config = {
        "from_attributes": True
    }