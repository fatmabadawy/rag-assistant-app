"""Shared RAG components used by the notebook, the index builder and the backend."""

from .chunking import CHUNK_OVERLAP, CHUNK_SIZE, Chunk, chunk_corpus, chunk_document
from .indexer import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    build_index,
    embed_texts,
    get_collection,
    load_index_config,
    search,
)
from .loader import Document, LoadError, clean_text, load_corpus, load_file
from .prompts import (
    MIN_SCORE,
    NO_CONTEXT_ANSWER,
    build_messages,
    cited_sources,
    filter_by_score,
    format_context,
)

__all__ = [
    "CHUNK_OVERLAP", "CHUNK_SIZE", "Chunk", "chunk_corpus", "chunk_document",
    "COLLECTION_NAME", "EMBEDDING_MODEL", "build_index", "embed_texts",
    "get_collection", "load_index_config", "search",
    "Document", "LoadError", "clean_text", "load_corpus", "load_file",
    "MIN_SCORE", "NO_CONTEXT_ANSWER", "build_messages", "cited_sources",
    "filter_by_score", "format_context",
]
