"""Thin wrapper around the backend API.

Keeping HTTP concerns out of app.py means the Streamlit code deals only with
rendering, and the base URL is read from the environment in exactly one place.
"""

from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_TIMEOUT = 180  # a small local LLM on CPU can genuinely take a while


class APIError(Exception):
    """Any failure talking to the backend, with a message safe to show a user."""


def get_base_url() -> str:
    """Backend URL from the environment. Never hard-coded at a call site."""
    url = os.getenv("API_BASE_URL")
    if not url:
        raise APIError(
            "API_BASE_URL is not set. Copy frontend/.env.example to frontend/.env."
        )
    return url.rstrip("/")


def health() -> dict:
    """GET /health. Raises APIError if the backend is not reachable."""
    try:
        response = requests.get(f"{get_base_url()}/health", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as exc:
        raise APIError(
            f"Cannot reach the backend at {get_base_url()}. "
            "Is uvicorn running on port 8000?"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise APIError(f"Health check failed: {exc}") from exc


def ask(question: str, top_k: int | None = None) -> dict:
    """POST /query and return the parsed response."""
    payload: dict = {"question": question}
    if top_k is not None:
        payload["top_k"] = top_k

    try:
        response = requests.post(
            f"{get_base_url()}/query", json=payload, timeout=DEFAULT_TIMEOUT
        )
    except requests.exceptions.ConnectionError as exc:
        raise APIError(
            f"Cannot reach the backend at {get_base_url()}. "
            "Start it with: uvicorn app.main:app --reload"
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise APIError(
            "The backend took too long to respond. A local model on CPU can be "
            "slow — try a smaller Ollama model such as llama3.2:1b."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise APIError(f"Request failed: {exc}") from exc

    if response.status_code == 422:
        raise APIError("That question was rejected as invalid — it may be too short.")
    if response.status_code == 503:
        detail = _detail(response)
        raise APIError(f"The backend is not ready: {detail}")
    if not response.ok:
        raise APIError(f"Backend returned {response.status_code}: {_detail(response)}")

    return response.json()


def _detail(response) -> str:
    try:
        return response.json().get("detail", response.text)
    except ValueError:
        return response.text
