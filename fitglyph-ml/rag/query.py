"""
RAG query engine.

Retrieves top-k relevant chunks from ChromaDB for a given question,
optionally injects workout log context when the queried exercise exists
in the user's history, then calls the LLM (Groq llama-3.3-70b-versatile)
with a structured technique-focused prompt.

Retrieval config (from ML_FEATURES.md):
  - Embedding model : all-MiniLM-L6-v2
  - Chunk size      : 400 tokens, 50-token overlap  (set at ingest time)
  - Top-k           : 5 documents per query
  - Similarity threshold : 0.72  (cosine; distance <= 0.28)
  - Workout context : injected into system prompt when exercise found in user history
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from rag.ingest import get_collection, get_embedder

router = APIRouter()

# ── Config ────────────────────────────────────────────────────────────────────
TOP_K               = 5
SIMILARITY_THRESHOLD = 0.72
DISTANCE_THRESHOLD   = 1.0 - SIMILARITY_THRESHOLD   # 0.28 for cosine distance

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")


# ── Request / Response models ─────────────────────────────────────────────────

class RAGQuery(BaseModel):
    question:      str
    exercise_hint: Optional[str] = None
    user_id:       Optional[int] = None


# ── Workout context ───────────────────────────────────────────────────────────

def _get_workout_context(user_id: int, exercise_hint: str) -> Optional[str]:
    """
    Query the SQLite workout DB for recent history of exercise_hint for this user.

    Returns a single-sentence context string, or None if no history found
    or if the DB is unavailable.
    """
    if not DATABASE_URL or not user_id or not exercise_hint:
        return None

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

        # Build a LIKE pattern to match exercise name variants (case-insensitive)
        pattern = f"%{exercise_hint.strip()}%"

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        COUNT(*)                      AS session_count,
                        MAX(e.weight)                 AS max_weight,
                        MAX(w.date)                   AS last_date
                    FROM exercise e
                    JOIN workout  w ON e.workout_id = w.id
                    WHERE w.user_id   = :uid
                      AND e.name LIKE :pattern
                      AND w.date     >= DATE('now', '-90 days')
                """),
                {"uid": user_id, "pattern": pattern},
            ).fetchone()

        if result and result[0] and result[0] > 0:
            count      = result[0]
            max_weight = result[1]
            context    = (
                f"User has logged {exercise_hint} {count} time"
                f"{'s' if count != 1 else ''} in the past 90 days."
            )
            if max_weight:
                context += f" Recent logged max: {max_weight} lbs."
            return context

    except Exception:
        pass

    return None


# ── Retrieval ─────────────────────────────────────────────────────────────────

def _retrieve(question: str, n_results: int = TOP_K) -> list[dict]:
    """
    Embed the question and query ChromaDB for the top-n most similar chunks.

    Returns only chunks whose cosine distance is <= DISTANCE_THRESHOLD
    (i.e., cosine similarity >= SIMILARITY_THRESHOLD).
    Returns an empty list if the collection is empty or unavailable.
    """
    try:
        collection = get_collection()
        if collection.count() == 0:
            return []

        embedder  = get_embedder()
        query_vec = embedder.encode(question).tolist()

        results = collection.query(
            query_embeddings=[query_vec],
            n_results=min(n_results, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        chunks: list[dict] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances",  [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            if dist <= DISTANCE_THRESHOLD:
                chunks.append({
                    "text":          doc,
                    "source":        meta.get("source", "Unknown"),
                    "exercise_name": meta.get("exercise_name", ""),
                    "url":           meta.get("url", "") or None,
                    "distance":      dist,
                })

        return chunks

    except Exception:
        return []


# ── Prompt building ───────────────────────────────────────────────────────────

def _build_messages(
    question:       str,
    chunks:         list[dict],
    workout_context: Optional[str],
) -> list[dict]:
    """
    Build a LangChain-compatible message list for the LLM.

    System prompt instructs the model to act as a precision technique
    assistant, cite sources by name, and decline to speculate beyond
    the provided context.
    """
    system_content = (
        "You are a precision exercise technique assistant for FitGlyph, a performance "
        "training app used by serious athletes. Answer questions based strictly on the "
        "provided source excerpts. Cite sources by their name (e.g., ExRx, ACE) when "
        "referencing specific information. If the provided context is insufficient to "
        "answer the question, say so directly — do not speculate or invent information. "
        "Be concise, specific, and data-precise. Avoid motivational language."
    )

    if workout_context:
        system_content += f"\n\nUser training context: {workout_context}"

    # Format retrieved chunks as numbered source blocks
    source_block = "\n\n".join(
        f"[Source {i + 1} — {c['source']}]\n{c['text']}"
        for i, c in enumerate(chunks)
    )

    human_content = f"Question: {question}\n\nSources:\n{source_block}"

    return [
        {"role": "system",    "content": system_content},
        {"role": "user",      "content": human_content},
    ]


# ── LLM call ─────────────────────────────────────────────────────────────────

def _call_llm(messages: list[dict]) -> str:
    """
    Call Groq via langchain_groq. Returns the answer string.
    Raises on error — caller handles graceful degradation.
    """
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage

    lc_messages = []
    for m in messages:
        if m["role"] == "system":
            lc_messages.append(SystemMessage(content=m["content"]))
        else:
            lc_messages.append(HumanMessage(content=m["content"]))

    llm      = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=GROQ_API_KEY)
    response = llm.invoke(lc_messages)
    return response.content


# ── FastAPI route ─────────────────────────────────────────────────────────────

@router.post("/query")
async def rag_query(body: RAGQuery):
    """
    POST /api/ml/rag/query

    Body:
        question      : str           — the user's technique / exercise question
        exercise_hint : str | null    — exercise name for workout context lookup
        user_id       : int | null    — injected by Flask proxy from session

    Response:
        answer              : str
        citations           : [{ source, excerpt, url }]
        workout_context_used: bool
    """
    question      = body.question.strip()
    exercise_hint = (body.exercise_hint or "").strip() or None
    user_id       = body.user_id

    if not question:
        return JSONResponse(
            status_code=422,
            content={"error": "empty_question", "message": "Question must not be empty."},
        )

    # ── Retrieve ──────────────────────────────────────────────────────────────
    chunks = _retrieve(question)

    if not chunks:
        return JSONResponse(
            content={
                "answer": (
                    "The exercise library doesn't have enough context to answer this "
                    "question. Try asking about a specific lift technique, common errors, "
                    "or muscle activation cues for the main barbell movements."
                ),
                "citations":            [],
                "workout_context_used": False,
            }
        )

    # ── Workout context ───────────────────────────────────────────────────────
    workout_context     = None
    workout_context_used = False

    if exercise_hint and user_id:
        workout_context = _get_workout_context(user_id, exercise_hint)
        if workout_context:
            workout_context_used = True

    # ── Build citations ───────────────────────────────────────────────────────
    citations = []
    seen_sources: set[str] = set()
    for chunk in chunks:
        source = chunk["source"]
        # Deduplicate by source name — keep the first (closest) excerpt per source
        if source not in seen_sources:
            seen_sources.add(source)
            citations.append({
                "source":  source,
                "excerpt": chunk["text"][:200].replace("\n", " "),
                "url":     chunk["url"],
            })

    # ── LLM synthesis ─────────────────────────────────────────────────────────
    if not GROQ_API_KEY:
        # Degrade gracefully: return stitched excerpts without LLM synthesis
        raw_answer = "\n\n".join(
            f"[{c['source']}] {c['text'][:400]}" for c in chunks[:3]
        )
        return JSONResponse(
            content={
                "answer":               raw_answer,
                "citations":            citations,
                "workout_context_used": workout_context_used,
            }
        )

    try:
        messages = _build_messages(question, chunks, workout_context)
        answer   = _call_llm(messages)
    except Exception as exc:
        # LLM failure — fall back to raw excerpts, never 500
        raw_answer = "\n\n".join(
            f"[{c['source']}] {c['text'][:400]}" for c in chunks[:3]
        )
        return JSONResponse(
            content={
                "answer":               raw_answer,
                "citations":            citations,
                "workout_context_used": workout_context_used,
            }
        )

    return JSONResponse(
        content={
            "answer":               answer,
            "citations":            citations,
            "workout_context_used": workout_context_used,
        }
    )
