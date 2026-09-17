"""Test fixtures.

The tests run without Ollama and without a built vector store: both services are
replaced with in-memory fakes after startup. That keeps the suite fast,
deterministic and runnable in CI, and it tests the API contract rather than the
quality of the model.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
for path in (str(REPO_ROOT), str(BACKEND_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from app.main import app as fastapi_app  # noqa: E402
from app.services.generation import GenerationError  # noqa: E402

SAMPLE_HIT = {
    "chunk_id": "02_databases.md::c07",
    "source": "02_databases.md",
    "text": (
        "A composite index on (a, b) can serve queries filtering on a alone or on "
        "a and b together, but not on b alone. This is the leftmost prefix rule."
    ),
    "score": 0.81,
}


class FakeRetrieval:
    def __init__(self, hits=None):
        self.hits = SAMPLE_HIT if hits is None else hits
        self.config = {"n_chunks": 35, "n_sources": 5, "embedding_model": "fake-model"}
        self._hits = [SAMPLE_HIT] if hits is None else hits

    @property
    def is_ready(self) -> bool:
        return True

    def retrieve(self, question: str, top_k: int):
        return self._hits[:top_k]


class EmptyRetrieval(FakeRetrieval):
    def __init__(self):
        super().__init__(hits=[])


class UnloadedRetrieval(FakeRetrieval):
    @property
    def is_ready(self) -> bool:
        return False


class FakeGeneration:
    def ping(self) -> bool:
        return True

    def generate(self, question: str, hits):
        if not hits:
            from rag_core import NO_CONTEXT_ANSWER

            return NO_CONTEXT_ANSWER, [], False
        return (
            "A composite index on (a, b) serves filters on a, or on a and b, "
            "but not on b alone [1].",
            [f"{hit['source']} ({hit['chunk_id']})" for hit in hits],
            True,
        )


class BrokenGeneration(FakeGeneration):
    def generate(self, question: str, hits):
        raise GenerationError("could not reach the Ollama model 'llama3.2:3b'")


@pytest.fixture
def client():
    """TestClient with both services faked out."""
    with TestClient(fastapi_app) as test_client:
        fastapi_app.state.retrieval = FakeRetrieval()
        fastapi_app.state.generation = FakeGeneration()
        yield test_client


@pytest.fixture
def app():
    return fastapi_app
