"""Embedding generation and the persisted Chroma vector store.

The vector store is written to disk once by the notebook (or scripts/build_index.py)
and loaded read-only by the FastAPI backend at startup. Nothing is re-embedded at
request time except the user's question.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from .chunking import CHUNK_OVERLAP, CHUNK_SIZE, Chunk

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "documents"
CONFIG_FILENAME = "index_config.json"

_model_cache: dict[str, object] = {}


def get_embedding_model(name: str = EMBEDDING_MODEL):
    """Load the sentence-transformer model once per process."""
    if name not in _model_cache:
        from sentence_transformers import SentenceTransformer

        _model_cache[name] = SentenceTransformer(name)
    return _model_cache[name]


def embed_texts(texts: list[str], model_name: str = EMBEDDING_MODEL) -> list[list[float]]:
    """Embed a list of strings into normalised vectors.

    Normalising means Chroma's cosine distance is a clean 0-2 range and
    similarity is simply 1 - distance.
    """
    model = get_embedding_model(model_name)
    vectors = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=len(texts) > 64,
        normalize_embeddings=True,
    )
    return [vector.tolist() for vector in vectors]


def _client(persist_dir: str | Path):
    # Chroma reads this at import time; the Settings flag alone does not stop the
    # client-start event, whose posthog call fails noisily on some versions.
    os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

    import chromadb
    from chromadb.config import Settings

    # chromadb 0.5.x calls a posthog API that newer posthog releases changed;
    # the failure is harmless but logs an ERROR on every call. requirements.txt
    # pins a compatible posthog, and this silences it if an incompatible one
    # slips in anyway.
    logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)

    # Telemetry off: it is not needed, and its failures spam stderr during demos.
    return chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )


def build_index(
    chunks: list[Chunk],
    persist_dir: str | Path,
    model_name: str = EMBEDDING_MODEL,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> dict:
    """Embed every chunk and persist it to a Chroma collection on disk.

    Also writes index_config.json next to the store so the backend can assert it
    is loading a store built with the same embedding model. A mismatch here is
    the single most common cause of silently terrible retrieval.
    """
    if not chunks:
        raise ValueError("no chunks to index - check your corpus directory")

    persist_dir = Path(persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    client = _client(persist_dir)
    # Rebuild from scratch so re-running the notebook is idempotent.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    embeddings = embed_texts([chunk.text for chunk in chunks], model_name=model_name)

    # Chroma recommends batching adds; 500 keeps memory flat on modest laptops.
    batch = 500
    for start in range(0, len(chunks), batch):
        window = chunks[start:start + batch]
        collection.add(
            ids=[chunk.chunk_id for chunk in window],
            documents=[chunk.text for chunk in window],
            embeddings=embeddings[start:start + batch],
            metadatas=[chunk.to_metadata() for chunk in window],
        )

    config = {
        "embedding_model": model_name,
        "collection_name": COLLECTION_NAME,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "n_chunks": len(chunks),
        "n_sources": len({chunk.source for chunk in chunks}),
        "distance": "cosine",
    }
    (persist_dir / CONFIG_FILENAME).write_text(json.dumps(config, indent=2))
    return config


def load_index_config(persist_dir: str | Path) -> dict:
    path = Path(persist_dir) / CONFIG_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found - run the notebook or scripts/build_index.py first"
        )
    return json.loads(path.read_text())


def get_collection(persist_dir: str | Path, expected_model: str | None = None):
    """Open the persisted collection, verifying the embedding model matches."""
    config = load_index_config(persist_dir)
    if expected_model and config["embedding_model"] != expected_model:
        raise ValueError(
            "embedding model mismatch: the store was built with "
            f"{config['embedding_model']} but the backend is configured for "
            f"{expected_model}. Rebuild the index or fix EMBEDDING_MODEL in .env."
        )
    return _client(persist_dir).get_collection(config["collection_name"])


def search(
    collection,
    question: str,
    top_k: int = 4,
    model_name: str = EMBEDDING_MODEL,
) -> list[dict]:
    """Return the top_k most similar chunks as plain dicts."""
    query_vector = embed_texts([question], model_name=model_name)[0]
    raw = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    hits: list[dict] = []
    for text, metadata, distance in zip(
        raw["documents"][0], raw["metadatas"][0], raw["distances"][0]
    ):
        hits.append(
            {
                "chunk_id": metadata["chunk_id"],
                "source": metadata["source"],
                "text": text,
                "score": round(1.0 - float(distance), 4),
            }
        )
    return hits
