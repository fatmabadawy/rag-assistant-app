#!/usr/bin/env python3
"""Run the evaluation set end-to-end and write docs/evaluation_results.md.

Requires a built vector store and a running Ollama. Use --retrieval-only to skip
generation and measure retrieval alone (no Ollama needed).

Usage:
    python scripts/run_evaluation.py
    python scripts/run_evaluation.py --retrieval-only
    python scripts/run_evaluation.py --top-k 6 --model llama3.2:1b
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from rag_core import (  # noqa: E402
    EMBEDDING_MODEL,
    MIN_SCORE,
    NO_CONTEXT_ANSWER,
    build_messages,
    filter_by_score,
    get_collection,
    load_index_config,
    search,
)
from rag_core.evaluation import (  # noqa: E402
    TEST_QUESTIONS,
    score_answer,
    score_retrieval,
    summarise,
    to_markdown_table,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--store", default=str(REPO_ROOT / "backend" / "data" / "vector_store")
    )
    parser.add_argument("--out", default=str(REPO_ROOT / "docs" / "evaluation_results.md"))
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--min-score", type=float, default=MIN_SCORE)
    parser.add_argument("--model", default="llama3.2:3b")
    parser.add_argument("--host", default="http://localhost:11434")
    parser.add_argument("--retrieval-only", action="store_true")
    args = parser.parse_args()

    config = load_index_config(args.store)
    collection = get_collection(args.store)

    client = None
    if not args.retrieval_only:
        import ollama

        client = ollama.Client(host=args.host, timeout=180)

    rows: list[dict] = []
    for question in TEST_QUESTIONS:
        hits = filter_by_score(
            search(collection, question.question, top_k=args.top_k,
                   model_name=config["embedding_model"]),
            min_score=args.min_score,
        )
        retrieval_ok = score_retrieval(question, hits)

        if args.retrieval_only:
            answer = "(generation skipped)"
            answer_ok, reason = retrieval_ok, "retrieval-only run"
        elif not hits:
            answer = NO_CONTEXT_ANSWER
            answer_ok, reason = score_answer(question, answer)
        else:
            response = client.chat(
                model=args.model,
                messages=build_messages(question.question, hits),
                options={"temperature": 0.1, "num_predict": 400},
            )
            answer = response["message"]["content"].strip()
            answer_ok, reason = score_answer(question, answer)

        rows.append(
            {
                "id": question.id,
                "question": question.question,
                "in_domain": question.in_domain,
                "expected_source": question.expected_source,
                "top_source": hits[0]["source"] if hits else None,
                "top_score": hits[0]["score"] if hits else 0.0,
                "answer": answer,
                "retrieval_ok": retrieval_ok,
                "answer_ok": answer_ok,
                "reason": reason,
            }
        )
        flag = "PASS" if answer_ok else "FAIL"
        print(f"[{flag}] {question.id}  {question.question[:60]}")

    metrics = summarise(rows)
    print("\nSummary:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "\n".join(
            [
                "# Evaluation Results",
                "",
                f"Generated: {datetime.now():%Y-%m-%d %H:%M}",
                "",
                "## Configuration",
                "",
                f"- Embedding model: `{config['embedding_model']}`",
                f"- LLM: `{args.model}`" + (" _(not run)_" if args.retrieval_only else ""),
                f"- Chunk size / overlap: {config['chunk_size']} / {config['chunk_overlap']}",
                f"- Chunks indexed: {config['n_chunks']} from {config['n_sources']} sources",
                f"- top_k: {args.top_k}, min_score: {args.min_score}",
                "",
                "## Metrics",
                "",
                "| Metric | Value |",
                "|---|---|",
                *[f"| {k.replace('_', ' ')} | {v} |" for k, v in metrics.items()],
                "",
                "## Per-question results",
                "",
                to_markdown_table(rows),
                "",
            ]
        )
    )
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
