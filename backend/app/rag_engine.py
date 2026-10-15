"""
rag_engine.py
-------------
A minimal Retrieval-Augmented Generation (RAG) pipeline, built with plain
Python only (no numpy/pandas, no vector database) so every step is visible.

GEN AI COURSE CONCEPTS USED:
1. Tokenization        -> splitting text into words
2. Embeddings          -> turning text into a numeric vector (here: a simple
                           bag-of-words / term-frequency vector, which is the
                           conceptual ancestor of the dense embeddings you'll
                           get from models like OpenAI's text-embedding-3)
3. Vector similarity    -> cosine similarity, computed by hand with math.sqrt
                           instead of numpy, so you can see exactly what a
                           vector database does under the hood
4. Retrieval            -> finding the most relevant document(s) for a query
5. Augmentation         -> injecting that retrieved context into a prompt
                           before it goes to the LLM (see ai_explainer.py)

In a production system, step 2 would use a real embedding model and step 3
would use a vector database like Pinecone, Weaviate, or pgvector. The logic
is identical — only the vector quality and search speed change at scale.
"""

import json
import math
import re
from pathlib import Path
from typing import Dict, List

GUIDELINES_PATH = Path(__file__).parent.parent / "data" / "guidelines.json"


def load_guidelines() -> List[Dict]:
    with open(GUIDELINES_PATH, "r") as f:
        return json.load(f)


def tokenize(text: str) -> List[str]:
    """Very simple tokenizer: lowercase + split on non-letters."""
    return re.findall(r"[a-zA-Z]+", text.lower())


def to_vector(tokens: List[str]) -> Dict[str, int]:
    """Bag-of-words vector as a dict: {word: count}.
    This is the simplest possible 'embedding' — just word frequency."""
    vec: Dict[str, int] = {}
    for tok in tokens:
        vec[tok] = vec.get(tok, 0) + 1
    return vec


def cosine_similarity(vec_a: Dict[str, int], vec_b: Dict[str, int]) -> float:
    """Cosine similarity between two sparse bag-of-words vectors,
    implemented with plain math (dot product / product of magnitudes)."""
    shared_words = set(vec_a.keys()) & set(vec_b.keys())
    dot_product = sum(vec_a[w] * vec_b[w] for w in shared_words)

    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot_product / (mag_a * mag_b)


class RAGEngine:
    """Retrieves the most relevant secure-coding guideline for a given
    vulnerability category or finding text."""

    def __init__(self):
        self.guidelines = load_guidelines()
        # Pre-compute embeddings for every guideline once at startup —
        # same idea as indexing documents into a vector database.
        self.index = [
            {**g, "vector": to_vector(tokenize(g["category"] + " " + g["text"]))}
            for g in self.guidelines
        ]

    def retrieve(self, query: str, top_k: int = 1) -> List[Dict]:
        query_vec = to_vector(tokenize(query))

        scored = []
        for doc in self.index:
            score = cosine_similarity(query_vec, doc["vector"])
            scored.append((score, doc))

        # Highest similarity first — same concept as a vector DB's nearest-
        # neighbor search, just done with a plain Python sort.
        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            {"id": doc["id"], "category": doc["category"], "text": doc["text"], "score": round(score, 3)}
            for score, doc in scored[:top_k]
        ]


# Simple category shortcut: since our scanner already tags each finding
# with a category (e.g. "SQL Injection"), we can retrieve by category
# directly for speed, and fall back to full similarity search otherwise.
def retrieve_guideline_for_category(engine: RAGEngine, category: str) -> Dict:
    for doc in engine.index:
        if doc["category"].lower() == category.lower():
            return {"id": doc["id"], "category": doc["category"], "text": doc["text"], "score": 1.0}
    # fallback to similarity search if no exact category match
    results = engine.retrieve(category, top_k=1)
    return results[0] if results else {"id": None, "category": category, "text": "No specific guideline found.", "score": 0.0}
