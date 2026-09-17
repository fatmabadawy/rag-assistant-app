#!/usr/bin/env python3
"""Build the persisted vector store from a corpus directory.

The notebook is the report; this script is the same pipeline as a one-liner, so
the index can be rebuilt in CI or by a grader who does not want to open Jupyter.

Usage:
    python scripts/build_index.py
    python scripts/build_index.py --corpus data/raw --out backend/data/vector_store
    python scripts/build_index.py --chunk-size 600 --chunk-overlap 100
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from rag_core import (  # noqa: E402
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    build_index,
    chunk_corpus,
    load_corpus,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default=str(REPO_ROOT / "data" / "raw"))
    parser.add_argument(
        "--out", default=str(REPO_ROOT / "backend" / "data" / "vector_store")
    )
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=CHUNK_OVERLAP)
    parser.add_argument("--model", default=EMBEDDING_MODEL)
    args = parser.parse_args()

    print(f"Loading corpus from {args.corpus} ...")
    documents, failures = load_corpus(args.corpus)

    for name, reason in failures:
        print(f"  SKIPPED {name}: {reason}")

    if not documents:
        print("No readable documents found. Put PDFs, .md or .txt files in the corpus dir.")
        return 1

    total_chars = sum(doc.n_chars for doc in documents)
    total_pages = sum(doc.n_pages for doc in documents)
    print(f"  {len(documents)} documents, {total_pages} pages, {total_chars:,} characters")

    chunks = chunk_corpus(documents, size=args.chunk_size, overlap=args.chunk_overlap)
    avg = sum(len(c.text) for c in chunks) / len(chunks)
    print(f"Chunked into {len(chunks)} chunks (avg {avg:.0f} chars)")

    print(f"Embedding with {args.model} and writing to {args.out} ...")
    config = build_index(
        chunks,
        persist_dir=args.out,
        model_name=args.model,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    print("Done. Index config:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
