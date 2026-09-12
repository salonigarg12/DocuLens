from fastapi import FastAPI

from app.routes import (
    auth_router,
    chat_router,
    chats_router,
    messages_router,
    pdf_router,
    summary_router,
)
from app.services.runtime import lifespan


app = FastAPI(
    title="DocuLens API",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(chats_router)
app.include_router(pdf_router)
app.include_router(chat_router)
app.include_router(messages_router)
app.include_router(summary_router)


@app.get("/")
def root():
    return {
        "message": "DocuLens API is running."
    }