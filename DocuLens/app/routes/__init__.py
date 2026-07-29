from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.chats import router as chats_router
from app.routes.messages import router as messages_router
from app.routes.pdf import router as pdf_router
from app.routes.summary import router as summary_router

__all__ = [
    "auth_router",
    "chat_router",
    "chats_router",
    "messages_router",
    "pdf_router",
    "summary_router",
]