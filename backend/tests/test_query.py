"""API contract tests for /health and /query."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import (
    BrokenGeneration,
    EmptyRetrieval,
    FakeGeneration,
    FakeRetrieval,
    UnloadedRetrieval,
)


# ---------------------------------------------------------------- health ----

def test_health_reports_ok_when_store_loaded(client):
    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["vector_store_loaded"] is True
    assert body["n_chunks"] == 35


# ----------------------------------------------------------- happy path ----

def test_query_returns_grounded_answer_with_sources(client):
    response = client.post(
        "/query", json={"question": "What is the leftmost prefix rule?"}
    )
    assert response.status_code == 200

    body = response.json()
    assert body["grounded"] is True
    assert body["answer"]
    assert "[1]" in body["answer"]              # the answer carries a citation
    assert len(body["sources"]) == 1
    assert body["sources"][0].startswith("02_databases.md")
    assert body["chunks"][0]["score"] == pytest.approx(0.81)
    assert body["latency_ms"] >= 0


# --------------------------------------------------------- invalid input ----

def test_query_rejects_missing_question_with_422(client):
    response = client.post("/query", json={})
    assert response.status_code == 422


def test_query_rejects_too_short_question_with_422(client):
    response = client.post("/query", json={"question": "hi"})
    assert response.status_code == 422


def test_query_rejects_out_of_range_top_k_with_422(client):
    response = client.post("/query", json={"question": "valid question", "top_k": 99})
    assert response.status_code == 422


# ------------------------------------------------------- grounding guard ----

def test_query_refuses_when_nothing_clears_the_score_floor(app):
    with TestClient(app) as client:
        app.state.retrieval = EmptyRetrieval()
        app.state.generation = FakeGeneration()

        response = client.post(
            "/query", json={"question": "What is the share price of Apple?"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["sources"] == []
    assert "don't have anything" in body["answer"].lower()


# --------------------------------------------------------- failure modes ----

def test_query_returns_503_when_vector_store_missing(app):
    with TestClient(app) as client:
        app.state.retrieval = UnloadedRetrieval()
        app.state.generation = FakeGeneration()
        response = client.post("/query", json={"question": "any valid question"})

    assert response.status_code == 503
    assert "vector store" in response.json()["detail"].lower()


def test_query_returns_503_when_llm_unreachable(app):
    with TestClient(app) as client:
        app.state.retrieval = FakeRetrieval()
        app.state.generation = BrokenGeneration()
        response = client.post("/query", json={"question": "any valid question"})

    assert response.status_code == 503
    assert "ollama" in response.json()["detail"].lower()
