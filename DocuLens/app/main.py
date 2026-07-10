from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Query as QueryParam
from pydantic import BaseModel, Field
import pdfplumber
import uuid
import faiss
import numpy as np
import logging
import io
import magic

from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_FILE_SIZE   = 10 * 1024 * 1024   # 10 MB
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 100
RETRIEVAL_TOP_K = 5                  # was 1 — more context for the LLM
SUMMARY_CHUNKS  = 10                 # was 1 — sample across the whole doc

# ── Globals populated at startup ──────────────────────────────────────────────
google_client    = None
embedding_model  = None
documents: dict  = {}                # chat_id → {chunks, index}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load heavy resources once at startup, release at shutdown."""
    global google_client, embedding_model

    logger.info("Loading embedding model …")
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("Embedding model ready.")

    logger.info("Initialising Google GenAI client …")
    google_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    logger.info("Google GenAI client ready.")

    yield  # app runs here

    logger.info("Shutting down …")


app = FastAPI(lifespan=lifespan)


# ── Helpers ───────────────────────────────────────────────────────────────────

def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split *text* into overlapping character-level chunks."""
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start : start + size])
        start += size - overlap
    return chunks


def retrieve_relevant_chunks(
    question: str,
    chunks: list[str],
    index: faiss.IndexFlatL2,
    top_k: int = RETRIEVAL_TOP_K,
) -> list[str]:
    """Embed *question* and return the *top_k* most similar chunks."""
    q_emb = np.array(embedding_model.encode([question])).astype("float32")
    distances, indices = index.search(q_emb, top_k)

    # Fix #6 — FAISS returns -1 when fewer results exist than top_k
    return [chunks[i] for i in indices[0] if i != -1]


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Server running"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # Fix #4 — enforce file size limit
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    # Fix #7 — validate MIME type from file bytes, not the client header
    mime = magic.from_buffer(contents[:2048], mime=True)
    if mime != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Extract text
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as exc:
        logger.error("PDF extraction failed: %s", exc)
        raise HTTPException(status_code=422, detail="Could not parse PDF")

    if not text.strip():
        raise HTTPException(status_code=422, detail="No readable text found in PDF")

    # Embed and index
    chunks     = chunk_text(text)
    embeddings = np.array(embedding_model.encode(chunks)).astype("float32")
    index      = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    chat_id = str(uuid.uuid4())
    documents[chat_id] = {"chunks": chunks, "index": index}

    logger.info("Uploaded PDF: chat_id=%s  chunks=%d", chat_id, len(chunks))
    return {"message": "PDF uploaded successfully", "chat_id": chat_id}


class Query(BaseModel):
    # Fix #11 — validate question length
    question: str = Field(..., min_length=1, max_length=500)


@app.post("/chat")
async def chat(
    query: Query,
    chat_id: str = QueryParam(...),   # explicit query-param declaration
):
    if chat_id not in documents:
        # Fix #8 — proper HTTP status codes
        raise HTTPException(status_code=404, detail="No PDF found for this chat_id")

    stored     = documents[chat_id]
    # Fix #3 — retrieve multiple chunks for richer context
    relevant   = retrieve_relevant_chunks(query.question, stored["chunks"], stored["index"])
    context    = " ".join(relevant)[:3000]

    prompt = f"""You are a helpful PDF assistant.
Answer ONLY from the provided PDF content.
If the answer is not present, say: "I could not find this information in the document."

PDF Content:
{context}

Question:
{query.question}"""

    try:
        response = google_client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return {"answer": response.text}
    except Exception as exc:
        # Fix #9 — use logger instead of print
        logger.error("LLM call failed: %s", exc)
        raise HTTPException(status_code=502, detail="LLM request failed")


@app.post("/summarize")
async def summarize(chat_id: str = QueryParam(...)):
    if chat_id not in documents:
        raise HTTPException(status_code=404, detail="No PDF found for this chat_id")

    chunks = documents[chat_id]["chunks"]

    # Fix #2 — use multiple early chunks instead of only the first one
    text = " ".join(chunks[:SUMMARY_CHUNKS])[:4000]

    prompt = f"""Summarize the following PDF content clearly.

Include:
- Main topic
- Important points
- Key conclusions

PDF Content:
{text}"""

    try:
        response = google_client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return {"summary": response.text}
    except Exception as exc:
        logger.error("Summarize LLM call failed: %s", exc)
        raise HTTPException(status_code=502, detail="LLM request failed")