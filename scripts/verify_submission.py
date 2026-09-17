#!/usr/bin/env python3
"""Pre-submission self-check.

Verifies the deliverables checklist and the "common mistakes that lose points"
from the project brief. Run this before you commit, and again after cloning your
own repo into a fresh folder.

Usage:
    python scripts/verify_submission.py
    python scripts/verify_submission.py --skip-live   # skip backend/Ollama checks
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
results: list[tuple[str, str, str]] = []


def check(name: str, ok: bool, detail: str = "", warn_only: bool = False) -> bool:
    status = PASS if ok else (WARN if warn_only else FAIL)
    results.append((status, name, detail))
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    return ok


# ---------------------------------------------------------------- files ----

def check_deliverables() -> None:
    print("\nDeliverables")

    required = [
        ("notebooks/rag_pipeline.ipynb", "notebook"),
        ("backend/app/main.py", "FastAPI app"),
        ("backend/app/api/routes/query.py", "query routes"),
        ("backend/requirements.txt", "backend requirements"),
        ("backend/.env.example", "backend .env.example"),
        ("backend/tests/test_query.py", "backend tests"),
        ("frontend/app.py", "frontend app"),
        ("frontend/api_client.py", "frontend API client"),
        ("frontend/.env.example", "frontend .env.example"),
        ("frontend/requirements.txt", "frontend requirements"),
        ("README.md", "root README"),
        (".gitignore", ".gitignore"),
    ]
    for relative, label in required:
        check(label, (REPO_ROOT / relative).exists(), relative)


def check_notebook() -> None:
    print("\nNotebook")
    path = REPO_ROOT / "notebooks" / "rag_pipeline.ipynb"
    if not path.exists():
        check("notebook readable", False, "missing")
        return

    try:
        notebook = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        check("notebook is valid JSON", False, str(exc))
        return

    check("notebook is valid JSON", True, f"{len(notebook['cells'])} cells")

    text = " ".join(
        "".join(cell["source"]) for cell in notebook["cells"]
        if cell["cell_type"] == "markdown"
    )
    for section in ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"]:
        check(f"section {section} present", section in text)

    import ast
    bad = []
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        try:
            ast.parse("".join(cell["source"]))
        except SyntaxError:
            bad.append(index)
    check("all code cells parse", not bad, f"bad cells: {bad}" if bad else "")

    stale = [
        cell for cell in notebook["cells"]
        if cell["cell_type"] == "code" and cell.get("outputs")
    ]
    check(
        "notebook has saved outputs",
        bool(stale),
        f"{len(stale)} cells with output — run it before submitting" if not stale
        else f"{len(stale)} cells",
        warn_only=True,
    )


def check_common_mistakes() -> None:
    print("\nCommon mistakes from the brief")

    gitignore = (REPO_ROOT / ".gitignore").read_text() if (REPO_ROOT / ".gitignore").exists() else ""
    for pattern, label in [
        (".venv", ".venv ignored"),
        ("__pycache__", "__pycache__ ignored"),
        (".env", ".env ignored"),
        ("*.log", "*.log ignored"),
        ("vector_store", "vector store ignored"),
    ]:
        check(label, pattern in gitignore)

    # Hard-coded backend URL in the frontend
    offenders = []
    for path in (REPO_ROOT / "frontend").glob("*.py"):
        source = path.read_text()
        for line in source.splitlines():
            if "localhost:8000" in line and "os.getenv" not in line and not line.strip().startswith("#"):
                offenders.append(f"{path.name}: {line.strip()[:60]}")
    check("no hard-coded backend URL in frontend", not offenders, "; ".join(offenders))

    # Evaluation actually populated
    eval_path = REPO_ROOT / "docs" / "evaluation_results.md"
    populated = eval_path.exists() and "Placeholder" not in eval_path.read_text()
    check(
        "evaluation results generated",
        populated,
        "still a placeholder — run scripts/run_evaluation.py" if not populated else "",
    )

    # README placeholders left in
    readme = (REPO_ROOT / "README.md").read_text()
    leftovers = [
        marker for marker in ["<your-username>", "Add screenshots", "paste the metrics"]
        if marker in readme
    ]
    check(
        "README placeholders resolved",
        not leftovers,
        f"still present: {', '.join(leftovers)}" if leftovers else "",
        warn_only=True,
    )


def check_index_and_tests() -> None:
    print("\nIndex and tests")

    store = REPO_ROOT / "backend" / "data" / "vector_store"
    config = store / "index_config.json"
    if config.exists():
        data = json.loads(config.read_text())
        check("vector store built", True, f"{data['n_chunks']} chunks from {data['n_sources']} sources")
    else:
        check("vector store built", False, "run: python scripts/build_index.py")

    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=REPO_ROOT / "backend",
            capture_output=True,
            text=True,
            timeout=300,
        )
        last = [line for line in completed.stdout.strip().splitlines() if line][-1]
        check("pytest passes", completed.returncode == 0, last)
    except Exception as exc:  # noqa: BLE001
        check("pytest passes", False, str(exc))


def check_live_services() -> None:
    print("\nLive services")
    try:
        import requests
    except ImportError:
        check("requests available", False, "pip install requests", warn_only=True)
        return

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        body = response.json()
        check("backend reachable", response.ok, f"status={body.get('status')}")
        check("vector store loaded in backend", body.get("vector_store_loaded", False))
        check("Ollama reachable", body.get("llm_reachable", False), f"model={body.get('llm_model')}")
    except Exception:
        check("backend reachable", False, "start it: uvicorn app.main:app --reload", warn_only=True)


def check_git() -> None:
    print("\nGit")
    if not (REPO_ROOT / ".git").exists():
        check("git repository initialised", False, "run: git init", warn_only=True)
        return
    check("git repository initialised", True)

    try:
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30
        ).stdout.splitlines()
    except Exception:
        return

    bad = [
        path for path in tracked
        if path.startswith(".venv/")
        or "__pycache__" in path
        or path.endswith(".env")
        or "vector_store/" in path and not path.endswith(".gitkeep")
    ]
    check("no forbidden files tracked", not bad, ", ".join(bad[:5]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-live", action="store_true")
    args = parser.parse_args()

    print("=" * 66)
    print("RAG Document Assistant — pre-submission check")
    print("=" * 66)

    check_deliverables()
    check_notebook()
    check_common_mistakes()
    check_index_and_tests()
    if not args.skip_live:
        check_live_services()
    check_git()

    failures = [r for r in results if r[0] == FAIL]
    warnings = [r for r in results if r[0] == WARN]

    print("\n" + "=" * 66)
    print(f"{len(results) - len(failures) - len(warnings)} passed, "
          f"{len(warnings)} warnings, {len(failures)} failures")

    if failures:
        print("\nMust fix before submitting:")
        for _, name, detail in failures:
            print(f"  - {name}" + (f" ({detail})" if detail else ""))
    if warnings:
        print("\nWorth checking:")
        for _, name, detail in warnings:
            print(f"  - {name}" + (f" ({detail})" if detail else ""))

    print("=" * 66)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
