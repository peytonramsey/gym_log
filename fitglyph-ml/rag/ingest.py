"""
RAG corpus ingestion pipeline.

Loads documents from rag/corpus/*.json, chunks them using a sliding window
(400 tokens, 50-token overlap), embeds with sentence-transformers
all-MiniLM-L6-v2, and upserts into a persistent ChromaDB collection.

Run directly:
    python -m rag.ingest            # ingest new / changed documents
    python -m rag.ingest --rebuild  # drop and rebuild the collection from scratch
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from typing import Optional

import chromadb
import tiktoken
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────
COLLECTION_NAME = "exercise_guide"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE      = 400   # tokens
CHUNK_OVERLAP   = 50    # tokens
SIMILARITY_METRIC = "cosine"

_THIS_DIR   = pathlib.Path(__file__).parent
CORPUS_DIR  = _THIS_DIR / "corpus"
CHROMA_PATH = os.getenv(
    "CHROMA_STORE_PATH",
    str(_THIS_DIR / "chroma_store"),
)

# ── Module-level singletons (lazy-initialised) ────────────────────────────────
_client:     Optional[chromadb.PersistentClient] = None
_collection  = None
_embedder:   Optional[SentenceTransformer]       = None
_tokenizer   = None


# ── Singleton accessors ───────────────────────────────────────────────────────

def get_collection():
    """Return the persistent ChromaDB collection, creating it if needed."""
    global _client, _collection
    if _collection is not None:
        return _collection

    _client = chromadb.PersistentClient(path=CHROMA_PATH)
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": SIMILARITY_METRIC},
    )
    return _collection


def get_embedder() -> SentenceTransformer:
    """Return the lazy-loaded sentence-transformers model."""
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def _get_tokenizer():
    """Return the lazy-loaded tiktoken encoder."""
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = tiktoken.get_encoding("cl100k_base")
    return _tokenizer


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping token-window chunks.

    Returns a list of decoded string chunks. Each chunk is at most
    chunk_size tokens; consecutive chunks share overlap tokens.
    """
    enc    = _get_tokenizer()
    tokens = enc.encode(text)

    if len(tokens) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunks.append(enc.decode(tokens[start:end]))
        if end == len(tokens):
            break
        start += chunk_size - overlap

    return chunks


# ── Ingestion ─────────────────────────────────────────────────────────────────

def ingest_corpus(
    corpus_dir: str | pathlib.Path = CORPUS_DIR,
    rebuild: bool = False,
) -> int:
    """
    Ingest all *.json files in corpus_dir into the ChromaDB collection.

    Each JSON file must be a list of document objects matching the schema:
        {
            "id":       str,          # unique document ID
            "text":     str,          # full text to embed
            "metadata": {             # all fields are optional but encouraged
                "source":           str,
                "exercise_name":    str,
                "muscle_group":     str,
                "movement_pattern": str,
                "url":              str | null
            }
        }

    If rebuild=True, the collection is deleted and recreated first.
    Returns the total number of chunks upserted.
    """
    global _collection

    collection = get_collection()

    if rebuild:
        _client.delete_collection(COLLECTION_NAME)
        _collection = None
        collection  = get_collection()
        print(f"[ingest] Collection '{COLLECTION_NAME}' rebuilt.")

    corpus_dir = pathlib.Path(corpus_dir)
    json_files = sorted(corpus_dir.glob("*.json"))

    if not json_files:
        print(f"[ingest] No *.json files found in {corpus_dir}")
        return 0

    embedder        = get_embedder()
    total_upserted  = 0

    for json_path in json_files:
        try:
            docs = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[ingest] Skipping {json_path.name}: {exc}")
            continue

        for doc in docs:
            doc_id   = doc.get("id", "")
            text     = doc.get("text", "")
            metadata = doc.get("metadata", {})

            if not doc_id or not text:
                print(f"[ingest] Skipping malformed doc in {json_path.name}")
                continue

            # Sanitise metadata: ChromaDB requires all values to be str/int/float/bool,
            # and None is not allowed — replace None with empty string.
            clean_meta: dict = {
                k: (v if v is not None else "")
                for k, v in metadata.items()
            }

            chunks = chunk_text(text)

            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_c{i}" if len(chunks) > 1 else doc_id
                embedding = embedder.encode(chunk).tolist()

                collection.upsert(
                    ids        = [chunk_id],
                    embeddings = [embedding],
                    documents  = [chunk],
                    metadatas  = [clean_meta],
                )
                total_upserted += 1

        print(f"[ingest] {json_path.name} — {len(docs)} docs processed.")

    print(f"[ingest] Done. {total_upserted} chunks upserted into '{COLLECTION_NAME}'.")
    return total_upserted


def add_user_note(user_id: int, note_text: str, exercise_name: str) -> None:
    """
    Append a personal cue note to the corpus for a given exercise.

    The note is immediately embedded and upserted into the collection.
    Notes are stored with source='UserNote' and are retrievable alongside
    curated content.
    """
    import hashlib
    import time

    note_hash = hashlib.md5(note_text.encode()).hexdigest()[:8]
    note_id   = f"user-{user_id}-{exercise_name.lower().replace(' ', '-')}-{note_hash}"

    metadata = {
        "source":           "UserNote",
        "exercise_name":    exercise_name,
        "muscle_group":     "",
        "movement_pattern": "",
        "url":              "",
        "user_id":          str(user_id),
        "created_at":       str(int(time.time())),
    }

    collection = get_collection()
    embedder   = get_embedder()
    embedding  = embedder.encode(note_text).tolist()

    collection.upsert(
        ids        = [note_id],
        embeddings = [embedding],
        documents  = [note_text],
        metadatas  = [metadata],
    )


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    rebuild = "--rebuild" in sys.argv
    ingest_corpus(rebuild=rebuild)
