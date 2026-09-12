import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from google import genai
from sentence_transformers import SentenceTransformer

from app.config import (
    EMBEDDING_MODEL_NAME,
    GOOGLE_API_KEY,
)

logger = logging.getLogger(__name__)

google_client: genai.Client | None = None
embedding_model: SentenceTransformer | None = None

documents: dict[str, dict[str, Any]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load expensive resources once when the application starts."""

    global google_client, embedding_model

    logger.info("Loading embedding model...")

    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL_NAME
    )

    logger.info("Embedding model ready.")

    logger.info("Initialising Google GenAI client...")

    google_client = genai.Client(
        api_key=GOOGLE_API_KEY
    )

    logger.info("Google GenAI client ready.")

    yield

    logger.info("Shutting down DocuLens...")