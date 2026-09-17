"""Prompt construction for grounded, cited answers.

The whole point of RAG is that the model answers from the retrieved context and
not from its own parameters. Three things enforce that here:

1. The system prompt states the constraint explicitly and gives an escape hatch
   ("say you don't know") so the model is not cornered into inventing an answer.
2. Every context block is numbered, and the model is told to cite [1], [2] inline.
   A claim with no citation is visibly ungrounded to the reader.
3. A relevance floor (MIN_SCORE) - if nothing retrieved clears it, we never call
   the LLM at all and return the refusal directly. This removes the worst
   failure mode, where an off-topic question retrieves weakly-related chunks and
   the model politely hallucinates around them.
"""

from __future__ import annotations

MIN_SCORE = 0.25  # cosine similarity floor; below this we treat retrieval as a miss

NO_CONTEXT_ANSWER = (
    "I don't have anything in the indexed documents that answers that. "
    "Try rephrasing, or ask about a topic covered by the document set."
)

SYSTEM_PROMPT = """You are a document assistant. You answer strictly from the \
numbered CONTEXT passages given to you.

Rules:
- Use only facts present in the CONTEXT. Do not use outside knowledge.
- Cite the passage number in square brackets after each claim, like [1] or [2][3].
- If the CONTEXT does not contain the answer, reply exactly: \
"I don't have anything in the indexed documents that answers that."
- Do not invent sources, numbers, or citations.
- Answer in 2-5 sentences unless the question needs a list.
"""

_USER_TEMPLATE = """CONTEXT:
{context}

QUESTION: {question}

Answer using only the CONTEXT above, citing passage numbers."""


def format_context(hits: list[dict], max_chars: int = 4000) -> str:
    """Render retrieved chunks as a numbered context block.

    Truncated at max_chars so a large top_k cannot overflow a small local
    model's context window - passages are added in rank order, best first.
    """
    blocks: list[str] = []
    used = 0
    for position, hit in enumerate(hits, start=1):
        block = f"[{position}] (source: {hit['source']})\n{hit['text']}"
        if used + len(block) > max_chars and blocks:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def build_messages(question: str, hits: list[dict]) -> list[dict]:
    """Build the chat messages sent to Ollama."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": _USER_TEMPLATE.format(
                context=format_context(hits), question=question
            ),
        },
    ]


def filter_by_score(hits: list[dict], min_score: float = MIN_SCORE) -> list[dict]:
    """Drop hits below the relevance floor."""
    return [hit for hit in hits if hit["score"] >= min_score]


def cited_sources(hits: list[dict]) -> list[str]:
    """Unique source labels, in rank order, for the API response."""
    seen: list[str] = []
    for hit in hits:
        label = f"{hit['source']} ({hit['chunk_id']})"
        if label not in seen:
            seen.append(label)
    return seen
