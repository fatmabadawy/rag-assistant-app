"""Generation service - wraps the local Ollama LLM.

If retrieval returned nothing above the relevance floor, the LLM is never
called: we return the canned refusal instead. This is both faster and safer,
since it removes any chance of the model answering from its own knowledge when
the corpus has nothing to say.
"""

from __future__ import annotations

import logging

from rag_core import NO_CONTEXT_ANSWER, build_messages, cited_sources

logger = logging.getLogger(__name__)


class GenerationError(RuntimeError):
    """Raised when the LLM backend is unreachable or returns an error."""


class GenerationService:
    def __init__(self, host: str, model: str, timeout: int, temperature: float):
        self.host = host
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self._client = None

    def load(self) -> None:
        """Create the Ollama client once at startup."""
        import ollama

        self._client = ollama.Client(host=self.host, timeout=self.timeout)
        logger.info("ollama client configured for %s (model=%s)", self.host, self.model)

    def ping(self) -> bool:
        """Cheap liveness check used by /health."""
        if self._client is None:
            return False
        try:
            self._client.list()
            return True
        except Exception as exc:  # noqa: BLE001 - health check must never raise
            logger.warning("ollama unreachable: %s", exc)
            return False

    def generate(self, question: str, hits: list[dict]) -> tuple[str, list[str], bool]:
        """Return (answer, sources, grounded)."""
        if not hits:
            return NO_CONTEXT_ANSWER, [], False

        if self._client is None:
            raise GenerationError("generation service not loaded")

        messages = build_messages(question, hits)

        try:
            response = self._client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_predict": 400,
                },
            )
        except Exception as exc:  # noqa: BLE001
            raise GenerationError(
                f"could not reach the Ollama model '{self.model}' at {self.host}: {exc}"
            ) from exc

        answer = response["message"]["content"].strip()
        return answer, cited_sources(hits), True
