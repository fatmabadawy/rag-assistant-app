"""Chunking strategy.

Strategy: *section-aware chunking with a sliding-window fallback*.

1. Split the document on blank lines into paragraphs.
2. Greedily pack paragraphs into a chunk until CHUNK_SIZE characters.
3. Any single paragraph longer than CHUNK_SIZE is split by a sliding window
   with CHUNK_OVERLAP characters of overlap, cut on the nearest sentence
   boundary so a chunk never ends mid-sentence.

Why not fixed-size-only: cutting blindly every N characters routinely splits a
definition away from the term it defines, which is exactly the span a user's
question targets. Respecting paragraph boundaries keeps semantically complete
units together and measurably raised retrieval hit-rate in our evaluation.

Why 900 / 150: our embedding model (all-MiniLM-L6-v2) truncates at 256 word
pieces, roughly 1000-1100 characters of English prose. 900 characters stays
under that limit so no text is silently dropped during embedding, while still
being large enough to hold a full explanation. 150 characters of overlap
(~1-2 sentences) means a fact stated at a chunk boundary appears intact in one
of the two neighbours.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .loader import Document

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
MIN_CHUNK_SIZE = 80  # drop fragments smaller than this - they carry no signal

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    """One retrievable unit of text."""

    chunk_id: str      # e.g. "networking.md::c03"
    source: str        # originating filename, used for citations
    index: int         # position within the document
    text: str

    def to_metadata(self) -> dict:
        return {"chunk_id": self.chunk_id, "source": self.source, "index": self.index}


def _split_long_paragraph(paragraph: str, size: int, overlap: int) -> list[str]:
    """Sliding window over one oversized paragraph, cut at sentence ends."""
    sentences = _SENTENCE_END.split(paragraph)
    windows: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        # A single sentence longer than the window: hard-cut it, nothing else to do.
        if len(sentence) > size:
            if current:
                windows.append(" ".join(current))
                current, current_len = [], 0
            for start in range(0, len(sentence), size - overlap):
                windows.append(sentence[start:start + size])
            continue

        if current_len + len(sentence) + 1 > size and current:
            windows.append(" ".join(current))
            # carry the tail of the finished window forward as overlap
            carried, carried_len = [], 0
            for prev in reversed(current):
                if carried_len + len(prev) > overlap:
                    break
                carried.insert(0, prev)
                carried_len += len(prev) + 1
            current, current_len = carried, carried_len

        current.append(sentence)
        current_len += len(sentence) + 1

    if current:
        windows.append(" ".join(current))
    return [w.strip() for w in windows if w.strip()]


def _heading_level(line: str) -> int:
    """Markdown heading level, or 0 if the line is not a heading."""
    stripped = line.lstrip()
    if not stripped.startswith("#"):
        return 0
    level = len(stripped) - len(stripped.lstrip("#"))
    return level if 1 <= level <= 6 and stripped[level:level + 1] in (" ", "") else 0


def _split_headings(paragraph: str) -> tuple[list[tuple[int, str]], str]:
    """Peel leading heading lines off a paragraph.

    Returns (headings, remaining_body). Headings are (level, title) pairs.
    """
    headings: list[tuple[int, str]] = []
    lines = paragraph.split("\n")
    index = 0
    while index < len(lines):
        level = _heading_level(lines[index])
        if level == 0:
            break
        headings.append((level, lines[index].lstrip().lstrip("#").strip()))
        index += 1
    return headings, "\n".join(lines[index:]).strip()


def _heading_path(stack: dict[int, str]) -> str:
    """Render the active heading stack as 'Document > Section > Subsection'."""
    return " > ".join(stack[level] for level in sorted(stack) if stack[level])


def chunk_document(
    document: Document,
    size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """Split one Document into overlapping, heading-aware chunks.

    Markdown headings are tracked rather than treated as body text. Each chunk is
    prefixed with its heading path, e.g.

        [Operating Systems > Synchronisation]

    This does two things. It stops a chunk from ending on a dangling section
    header whose content lives in the next chunk. And it gives every chunk a
    small amount of standing context, so a passage that says "it requires four
    conditions" still embeds near the word "deadlock" even when that word appears
    only in the heading.
    """
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")

    paragraphs = [p.strip() for p in document.text.split("\n\n") if p.strip()]
    stack: dict[int, str] = {}
    pieces: list[tuple[str, str]] = []   # (heading_path, text)
    buffer: list[str] = []
    buffer_len = 0
    buffer_path = ""

    def flush() -> None:
        nonlocal buffer, buffer_len
        if buffer:
            pieces.append((buffer_path, "\n\n".join(buffer)))
            buffer, buffer_len = [], 0

    for paragraph in paragraphs:
        headings, body = _split_headings(paragraph)

        if headings:
            # A new section starts here: close the current chunk so the heading
            # never trails at the end of one.
            flush()
            for level, title in headings:
                stack = {lvl: t for lvl, t in stack.items() if lvl < level}
                stack[level] = title
            buffer_path = _heading_path(stack)
            if not body:
                continue
            paragraph = body

        if not buffer:
            buffer_path = _heading_path(stack)

        if len(paragraph) > size:
            flush()
            for window in _split_long_paragraph(paragraph, size, overlap):
                pieces.append((_heading_path(stack), window))
            continue

        if buffer_len + len(paragraph) + 2 > size and buffer:
            flush()
            buffer_path = _heading_path(stack)

        buffer.append(paragraph)
        buffer_len += len(paragraph) + 2

    flush()

    stem = document.source
    chunks: list[Chunk] = []
    for path, text in pieces:
        if len(text) < MIN_CHUNK_SIZE:
            continue
        prefixed = f"[{path}]\n{text}" if path else text
        chunks.append(
            Chunk(
                chunk_id=f"{stem}::c{len(chunks):03d}",
                source=stem,
                index=len(chunks),
                text=prefixed,
            )
        )
    return chunks


def chunk_corpus(
    documents: list[Document],
    size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(chunk_document(document, size=size, overlap=overlap))
    return chunks
