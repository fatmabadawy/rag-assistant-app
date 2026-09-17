"""API routes: GET /health and POST /query."""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.schemas.query import HealthResponse, QueryRequest, QueryResponse, RetrievedChunk
from app.services.generation import GenerationError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(request: Request) -> HealthResponse:
    """Liveness and readiness. Reports whether the store and LLM are usable."""
    settings = get_settings()
    retrieval = request.app.state.retrieval
    generation = request.app.state.generation

    return HealthResponse(
        status="ok" if retrieval.is_ready else "degraded",
        version=settings.app_version,
        vector_store_loaded=retrieval.is_ready,
        n_chunks=retrieval.config.get("n_chunks"),
        embedding_model=retrieval.config.get("embedding_model"),
        llm_model=settings.ollama_model,
        llm_reachable=generation.ping(),
    )


@router.post("/query", response_model=QueryResponse, tags=["rag"])
def query(payload: QueryRequest, request: Request) -> QueryResponse:
    """Retrieve relevant chunks, then generate an answer grounded in them."""
    settings = get_settings()
    retrieval = request.app.state.retrieval
    generation = request.app.state.generation

    if not retrieval.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not loaded. Build it with scripts/build_index.py.",
        )

    started = time.perf_counter()
    top_k = payload.top_k or settings.top_k

    hits = retrieval.retrieve(payload.question, top_k=top_k)

    try:
        answer, sources, grounded = generation.generate(payload.question, hits)
    except GenerationError as exc:
        logger.error("generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    return QueryResponse(
        answer=answer,
        sources=sources,
        chunks=[
            RetrievedChunk(
                chunk_id=hit["chunk_id"],
                source=hit["source"],
                score=hit["score"],
                preview=hit["text"][:300] + ("..." if len(hit["text"]) > 300 else ""),
            )
            for hit in hits
        ],
        grounded=grounded,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
