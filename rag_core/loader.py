"""Document loading and cleaning.

Supports .pdf (via pypdf), .md and .txt. Every loaded document keeps its
source filename so that retrieved chunks can be cited back to a real file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED_SUFFIXES = {".pdf", ".md", ".txt"}


@dataclass
class Document:
    """A single source document after text extraction."""

    source: str          # filename, used as the citation label
    text: str            # cleaned full text
    n_pages: int = 1     # pages for PDFs, 1 for plain text
    meta: dict = field(default_factory=dict)

    @property
    def n_chars(self) -> int:
        return len(self.text)


class LoadError(Exception):
    """Raised when a file exists but no usable text could be extracted."""


# --------------------------------------------------------------------------
# cleaning
# --------------------------------------------------------------------------

_MULTI_NEWLINE = re.compile(r"\n{3,}")
_TRAILING_SPACE = re.compile(r"[ \t]+\n")
_HYPHEN_LINEBREAK = re.compile(r"(\w)-\n(\w)")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_PAGE_NUMBER_LINE = re.compile(r"^\s*(page\s+)?\d{1,4}\s*$", re.IGNORECASE | re.MULTILINE)


def clean_text(raw: str) -> str:
    """Normalise whitespace and repair PDF extraction artefacts.

    PDF text extraction typically produces three problems that hurt retrieval:
    words split across lines by hyphenation, bare page-number lines that become
    noise chunks, and runs of blank lines that break paragraph detection.
    """
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = _HYPHEN_LINEBREAK.sub(r"\1\2", text)   # "re-\ntrieval" -> "retrieval"
    text = _PAGE_NUMBER_LINE.sub("", text)
    text = _TRAILING_SPACE.sub("\n", text)
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------
# per-format readers
# --------------------------------------------------------------------------

def _read_pdf(path: Path) -> tuple[str, int]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - environment problem
        raise LoadError("pypdf is not installed; run pip install pypdf") from exc

    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n\n".join(pages), len(pages)


def _read_plain(path: Path) -> tuple[str, int]:
    return path.read_text(encoding="utf-8", errors="replace"), 1


def load_file(path: str | Path) -> Document:
    """Load one file into a Document. Raises LoadError if it yields no text."""
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_SUFFIXES:
        raise LoadError(f"unsupported file type: {suffix}")

    raw, n_pages = _read_pdf(path) if suffix == ".pdf" else _read_plain(path)
    text = clean_text(raw)

    # A PDF of scanned images extracts as (almost) nothing. Flag it loudly
    # rather than silently indexing an empty document.
    if len(text) < 50:
        raise LoadError(
            f"{path.name}: extracted only {len(text)} characters - "
            "this is probably a scanned PDF that needs OCR"
        )

    return Document(source=path.name, text=text, n_pages=n_pages)


def load_corpus(directory: str | Path) -> tuple[list[Document], list[tuple[str, str]]]:
    """Load every supported file in a directory.

    Returns (documents, failures) where failures is a list of
    (filename, reason) so the notebook can report them honestly.
    """
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"corpus directory not found: {directory}")

    documents: list[Document] = []
    failures: list[tuple[str, str]] = []

    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        try:
            documents.append(load_file(path))
        except LoadError as exc:
            failures.append((path.name, str(exc)))

    return documents, failures
