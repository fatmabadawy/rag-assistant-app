"""Request and response models for the query API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural-language question to answer from the indexed documents.",
        examples=["What is the leftmost prefix rule for composite indexes?"],
    )
    top_k: int | None = Field(
        None, ge=1, le=10, description="Override the number of chunks to retrieve."
    )


class RetrievedChunk(BaseModel):
    chunk_id: str
    source: str
    score: float
    preview: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    chunks: list[RetrievedChunk] = []
    grounded: bool = Field(
        True, description="False when no chunk cleared the relevance floor."
    )
    latency_ms: int = 0


class HealthResponse(BaseModel):
    status: str
    version: str
    vector_store_loaded: bool
    n_chunks: int | None = None
    embedding_model: str | None = None
    llm_model: str
    llm_reachable: bool
