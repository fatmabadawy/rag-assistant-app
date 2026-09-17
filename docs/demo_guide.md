# Demo & Defence Guide

Notes for the live demo and the recorded walkthrough. **Read the code before the
demo** — the questions below are the ones a grader is most likely to ask, and
they all target decisions that are visible in the source.

## Before you start

1. `ollama serve` running, model pulled, `ollama list` confirms it.
2. `python scripts/build_index.py` has been run — `/health` shows `n_chunks`.
3. Backend up on 8000, frontend up on 8501.
4. Run your evaluation and have `docs/evaluation_results.md` populated.
5. Clone your own repo into a fresh folder and follow only the README. If any
   step fails, fix the README — this is an explicit grading criterion.

## A demo order that shows the system off

1. **`/health` first.** Proves the store is loaded and the LLM is reachable
   before you ask anything. It also frames the architecture.
2. **An easy in-domain question** — e.g. *"What is the leftmost prefix rule for
   composite indexes?"* Then expand *Retrieved passages* and point out the
   similarity scores and the `[n]` citations matching the passages.
3. **A harder concept-pair question** — *"What is the difference between flow
   control and congestion control?"* This needs two facts from one region and
   shows retrieval doing real work.
4. **An out-of-domain question** — *"What is the current share price of Apple?"*
   The assistant refuses. This is the moment to explain the score floor: the LLM
   was **never called**. A naive RAG system answers this one confidently and
   wrongly.
5. **Swagger UI** at `/docs`, send a request, show the 422 on an invalid body.
6. **`pytest -v`** — eight tests, sub-second, no Ollama needed.

## Questions you should be ready for

**"Why 900 characters and 150 overlap?"**
900 stays under `all-MiniLM-L6-v2`'s 256-token truncation limit (~1000–1100
characters). Past that, text is silently ignored during embedding — no error,
just worse retrieval. 150 characters is one to two sentences, enough for a fact
split across a boundary to survive intact in one of the two neighbours.

**"How do you know it's not just answering from the LLM's own knowledge?"**
Three things. The score floor means the LLM is never called when nothing relevant
is retrieved. The prompt requires a `[n]` citation per claim, so an uncited claim
is visibly ungrounded. And the evaluation set includes two out-of-domain
questions whose correct behaviour is a refusal — demo that live.

**"What happens if Ollama is down?"**
`/health` reports `llm_reachable: false`, `/query` returns 503 with a message
naming the host and model, and the frontend shows it as a friendly error rather
than a stack trace. Show it by stopping Ollama.

**"Why Chroma and not FAISS?"**
Chroma persists metadata alongside vectors with no extra code, which is what
makes citations possible — FAISS returns indices and you maintain the metadata
mapping yourself. At this corpus size the performance difference is irrelevant.

**"Why is there a `rag_core/` package instead of putting the code in the
notebook?"**
So chunking and prompting have exactly one definition. If the notebook chunked
one way and the backend another, the backend would be querying an index built
under different assumptions — a bug that produces quietly bad results rather than
an error.

**"What's your biggest failure case?"**
Answer from your *own* evaluation run, not from memory. Look at the FAIL rows in
`docs/evaluation_results.md` and be specific about what you'd change.

**"How would you improve it?"**
Reasonable answers: a reranker (cross-encoder) over the top-20 to improve
precision; hybrid search combining BM25 keyword matching with dense vectors for
exact terms like error codes; query rewriting for multi-hop questions; streaming
token-by-token responses; caching embeddings for repeated questions.

## Recording the walkthrough

Cover, in order: the problem, the architecture diagram, a fast pass through the
notebook's seven sections, the running app including the refusal case, the API
docs, the test suite, and your evaluation numbers with an honest note on what
failed. Keep it tight — narrate what you decided and why, not just what you
clicked.
