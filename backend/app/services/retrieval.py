"""Retrieval service.

The vector store and the embedding model are loaded exactly once, at application
startup, and held on the service instance. Loading a sentence-transformer costs
1-3 seconds; doing that per request would dominate latency and is the mistake
this service exists to avoid.
"""

from __future__ import annotations

import logging

from rag_core import filter_by_score, get_collection, search

logger = logging.getLogger(__name__)


class RetrievalService:
    """Owns the loaded Chroma collection for the lifetime of the process."""

    def __init__(self, vector_store_dir: str, embedding_model: str, min_score: float):
        self.vector_store_dir = vector_store_dir
        self.embedding_model = embedding_model
        self.min_score = min_score
        self.collection = None
        self.config: dict = {}

    def load(self) -> None:
        """Open the persisted store and warm the embedding model."""
        from rag_core import embed_texts, load_index_config

        self.config = load_index_config(self.vector_store_dir)
        self.collection = get_collection(
            self.vector_store_dir, expected_model=self.embedding_model
        )
        # Warm-up: force the model into memory now rather than on the first user
        # request, so the demo's first question is not artificially slow.
        embed_texts(["warm up"], model_name=self.embedding_model)
        logger.info(
            "vector store loaded: %s chunks from %s sources",
            self.config.get("n_chunks"),
            self.config.get("n_sources"),
        )

    @property
    def is_ready(self) -> bool:
        return self.collection is not None

    def retrieve(self, question: str, top_k: int) -> list[dict]:
        """Return chunks above the relevance floor, best first."""
        if not self.is_ready:
            raise RuntimeError("retrieval service not loaded")

        hits = search(
            self.collection,
            question,
            top_k=top_k,
            model_name=self.embedding_model,
        )
        kept = filter_by_score(hits, min_score=self.min_score)
        logger.info(
            "retrieved %d hits, %d above floor %.2f (top score %.3f)",
            len(hits),
            len(kept),
            self.min_score,
            hits[0]["score"] if hits else 0.0,
        )
        return kept
