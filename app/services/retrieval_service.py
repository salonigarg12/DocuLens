import faiss
import numpy as np

from app.config import RETRIEVAL_TOP_K
import app.services.runtime as runtime


def retrieve_relevant_chunks(
    question: str,
    chunks: list[str],
    index: faiss.Index,
    top_k: int = RETRIEVAL_TOP_K,
) -> list[str]:
    """Return the chunks most semantically similar to the question."""

    if runtime.embedding_model is None:
        raise RuntimeError(
            "Embedding model has not been initialized"
        )

    if not chunks:
        return []

    question_embedding = runtime.embedding_model.encode(
        [question]
    )

    question_embedding_array = np.asarray(
        question_embedding,
        dtype="float32",
    )

    actual_top_k = min(top_k, len(chunks))

    _, indices = index.search(
        question_embedding_array,
        actual_top_k,
    )

    return [
        chunks[index_position]
        for index_position in indices[0]
        if index_position != -1
    ]