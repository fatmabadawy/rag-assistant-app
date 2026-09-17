"""Streamlit chat interface for the RAG Document Assistant.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from api_client import APIError, ask, get_base_url, health

st.set_page_config(page_title="RAG Document Assistant", page_icon="📄", layout="centered")

SAMPLE_QUESTIONS = [
    "What is the leftmost prefix rule for composite indexes?",
    "What is the difference between flow control and congestion control?",
    "What four conditions are required for deadlock?",
    "Why do dynamic arrays double their capacity?",
]


# --------------------------------------------------------------- sidebar ----

def render_sidebar() -> int:
    with st.sidebar:
        st.header("Settings")

        try:
            st.caption(f"Backend: `{get_base_url()}`")
        except APIError as exc:
            st.error(str(exc))
            st.stop()

        top_k = st.slider(
            "Passages to retrieve",
            min_value=1,
            max_value=10,
            value=4,
            help="More passages give the model more to work with, but also more "
                 "chance to be distracted by a weakly related chunk.",
        )

        st.divider()
        st.subheader("Backend status")
        if st.button("Check connection", use_container_width=True):
            _render_health()

        st.divider()
        st.subheader("Try a question")
        for question in SAMPLE_QUESTIONS:
            if st.button(question, use_container_width=True, key=f"s-{question}"):
                st.session_state.pending_question = question
                st.rerun()

        st.divider()
        if st.button("Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    return top_k


def _render_health() -> None:
    try:
        info = health()
    except APIError as exc:
        st.error(str(exc))
        return

    if info["vector_store_loaded"]:
        st.success(f"Vector store: {info['n_chunks']} chunks loaded")
    else:
        st.error("Vector store not loaded — build the index first")

    if info["llm_reachable"]:
        st.success(f"Ollama: {info['llm_model']} reachable")
    else:
        st.error(f"Ollama not reachable (model {info['llm_model']})")


# ---------------------------------------------------------------- answer ----

def render_answer(payload: dict) -> None:
    if not payload.get("grounded", True):
        st.warning(payload["answer"])
    else:
        st.markdown(payload["answer"])

    sources = payload.get("sources", [])
    if sources:
        st.caption("Sources: " + " · ".join(f"`{source}`" for source in sources))

    chunks = payload.get("chunks", [])
    if chunks:
        with st.expander(f"Retrieved passages ({len(chunks)})"):
            for position, chunk in enumerate(chunks, start=1):
                st.markdown(
                    f"**[{position}] {chunk['source']}** — similarity "
                    f"`{chunk['score']:.3f}` · `{chunk['chunk_id']}`"
                )
                st.text(chunk["preview"])
                if position < len(chunks):
                    st.divider()

    if payload.get("latency_ms"):
        st.caption(f"Answered in {payload['latency_ms'] / 1000:.1f}s")


# ------------------------------------------------------------------ main ----

def main() -> None:
    st.title("📄 RAG Document Assistant")
    st.caption(
        "Ask a question about the indexed documents. Answers are generated only "
        "from retrieved passages, with citations — if the documents don't cover "
        "it, the assistant says so."
    )

    top_k = render_sidebar()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                render_answer(message["payload"])

    # A question comes either from the chat box or from a sidebar sample button.
    typed = st.chat_input("Ask a question about the documents...")
    question = typed or st.session_state.pop("pending_question", None)

    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving passages and generating a grounded answer..."):
            try:
                payload = ask(question, top_k=top_k)
            except APIError as exc:
                st.error(str(exc))
                st.session_state.messages.pop()  # don't keep a turn with no answer
                return

        render_answer(payload)

    st.session_state.messages.append({"role": "assistant", "payload": payload})


if __name__ == "__main__":
    main()
