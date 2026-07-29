from datetime import datetime

from pydantic import BaseModel, Field


class ChatCreate(BaseModel):
    chat_name: str = Field(min_length=1, max_length=255)


class ChatRename(BaseModel):
    chat_name: str = Field(min_length=1, max_length=255)


class ChatResponse(BaseModel):
    chat_id: str
    chat_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }