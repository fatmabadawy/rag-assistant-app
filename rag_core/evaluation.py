"""Evaluation harness for the RAG pipeline.

Two things are measured separately, because they fail for different reasons:

* **Retrieval quality** - did the correct source document appear in the top-k?
  Measured by `expected_source`. Needs no LLM, so it runs fast and is
  deterministic.
* **Answer grounding** - did the generated answer actually state the fact, and
  did it cite a passage? Measured by `expected_keywords` plus a citation check.
  Needs Ollama running.

The question set deliberately includes out-of-domain questions whose expected
behaviour is a refusal. A RAG system that answers those from the LLM's own
parametric knowledge has failed, even though the text it produces may be correct.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

CITATION_PATTERN = re.compile(r"\[\d+\]")


@dataclass
class TestQuestion:
    id: str
    question: str
    expected_source: str | None      # None means "should not be answerable"
    expected_keywords: list[str] = field(default_factory=list)
    note: str = ""

    @property
    def in_domain(self) -> bool:
        return self.expected_source is not None


# --------------------------------------------------------------------------
# The evaluation set. Replace these when you swap in your own corpus.
# --------------------------------------------------------------------------

TEST_QUESTIONS: list[TestQuestion] = [
    TestQuestion(
        "q01",
        "Why do dynamic arrays double their capacity instead of growing by a fixed amount?",
        "01_data_structures.md",
        ["amortis", "O(1)", "doubl"],
        "Requires reasoning stated explicitly in the text.",
    ),
    TestQuestion(
        "q02",
        "What is the difference between an AVL tree and a red-black tree?",
        "01_data_structures.md",
        ["balance", "rotation", "red-black"],
    ),
    TestQuestion(
        "q03",
        "At what load factor should a hash table be resized?",
        "01_data_structures.md",
        ["0.75", "load factor"],
        "Tests retrieval of a specific numeric fact.",
    ),
    TestQuestion(
        "q04",
        "What is the leftmost prefix rule for composite indexes?",
        "02_databases.md",
        ["composite", "prefix", "index"],
    ),
    TestQuestion(
        "q05",
        "Explain the difference between a non-repeatable read and a phantom read.",
        "02_databases.md",
        ["phantom", "non-repeatable", "rows"],
        "Two similar concepts - tests whether retrieval brings back both.",
    ),
    TestQuestion(
        "q06",
        "Why do relational databases use B+ trees rather than hash indexes?",
        "02_databases.md",
        ["range", "leaf", "B+"],
    ),
    TestQuestion(
        "q07",
        "What is the difference between flow control and congestion control in TCP?",
        "03_networking.md",
        ["receiver", "network", "window"],
        "Commonly confused pair - a good hallucination probe.",
    ),
    TestQuestion(
        "q08",
        "What does HTTP status code 422 mean?",
        "03_networking.md",
        ["422", "validation"],
    ),
    TestQuestion(
        "q09",
        "When should I optimise for recall instead of precision?",
        "04_machine_learning.md",
        ["recall", "missed", "screening"],
    ),
    TestQuestion(
        "q10",
        "Why is cosine similarity preferred over Euclidean distance for text embeddings?",
        "04_machine_learning.md",
        ["cosine", "magnitude", "angle"],
    ),
    TestQuestion(
        "q11",
        "What four conditions are required for deadlock?",
        "05_operating_systems.md",
        ["mutual exclusion", "hold and wait", "circular wait"],
        "Tests whether a list is retrieved intact rather than split across chunks.",
    ),
    TestQuestion(
        "q12",
        "What is Belady's anomaly?",
        "05_operating_systems.md",
        ["FIFO", "frames", "fault"],
    ),
    TestQuestion(
        "q13",
        "What is the current share price of Apple?",
        None,
        [],
        "Out of domain - the assistant must refuse, not answer from LLM knowledge.",
    ),
    TestQuestion(
        "q14",
        "Write me a Python function that reverses a string.",
        None,
        [],
        "Out of domain - a general LLM request the assistant must decline.",
    ),
]


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------

def is_refusal(answer: str) -> bool:
    lowered = answer.lower()
    return "don't have anything" in lowered or "do not have anything" in lowered


def score_retrieval(question: TestQuestion, hits: list[dict]) -> bool:
    """True if retrieval behaved correctly for this question."""
    sources = {hit["source"] for hit in hits}
    if question.in_domain:
        return question.expected_source in sources
    # Out of domain: correct behaviour is that nothing cleared the score floor.
    return len(hits) == 0


def score_answer(question: TestQuestion, answer: str) -> tuple[bool, str]:
    """Return (correct, reason) for a generated answer."""
    if not question.in_domain:
        if is_refusal(answer):
            return True, "correctly refused"
        return False, "answered an out-of-domain question (ungrounded)"

    if is_refusal(answer):
        return False, "refused a question the corpus does answer"

    lowered = answer.lower()
    missing = [kw for kw in question.expected_keywords if kw.lower() not in lowered]
    if missing:
        return False, f"missing expected content: {', '.join(missing)}"

    if not CITATION_PATTERN.search(answer):
        return False, "answer has no [n] citation"

    return True, "grounded and cited"


def summarise(rows: list[dict]) -> dict:
    """Aggregate metrics over evaluated rows."""
    total = len(rows)
    in_domain = [r for r in rows if r["in_domain"]]
    out_domain = [r for r in rows if not r["in_domain"]]

    return {
        "n_questions": total,
        "retrieval_hit_rate": _pct(sum(r["retrieval_ok"] for r in rows), total),
        "answer_accuracy": _pct(sum(r["answer_ok"] for r in rows), total),
        "in_domain_accuracy": _pct(
            sum(r["answer_ok"] for r in in_domain), len(in_domain)
        ),
        "refusal_accuracy": _pct(
            sum(r["answer_ok"] for r in out_domain), len(out_domain)
        ),
    }


def _pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{numerator}/{denominator} ({100 * numerator / denominator:.0f}%)"


def to_markdown_table(rows: list[dict]) -> str:
    """Render evaluated rows as the results table required by the brief."""
    header = (
        "| # | Question | Retrieved source (top-1) | Answer (truncated) | Correct? | Notes |\n"
        "|---|---|---|---|---|---|"
    )
    lines = [header]
    for row in rows:
        answer = row["answer"].replace("\n", " ").replace("|", "\\|")
        if len(answer) > 110:
            answer = answer[:107] + "..."
        question = row["question"].replace("|", "\\|")
        lines.append(
            f"| {row['id']} | {question} | {row['top_source'] or '_(none above floor)_'} "
            f"| {answer} | {'PASS' if row['answer_ok'] else 'FAIL'} | {row['reason']} |"
        )
    return "\n".join(lines)
