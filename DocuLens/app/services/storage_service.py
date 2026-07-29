import json
from pathlib import Path

import faiss

import app.services.runtime as runtime
from app.config import (
    CHUNKS_DIR,
    INDEXES_DIR,
)


def load_chat_resources(pdf_id: str):
    """
    Loads FAISS index and chunks from disk.
    """

    if pdf_id in runtime.documents:
        return runtime.documents[pdf_id]

    index_path = INDEXES_DIR / f"{pdf_id}.faiss"
    chunks_path = CHUNKS_DIR / f"{pdf_id}.json"

    if not index_path.exists():
        raise FileNotFoundError(index_path)

    if not chunks_path.exists():
        raise FileNotFoundError(chunks_path)

    index = faiss.read_index(str(index_path))

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    runtime.documents[pdf_id] = {
        "index": index,
        "chunks": chunks,
    }

    return runtime.documents[pdf_id]