"""
Retrieves the most relevant faq entries for a query using cosine
similarity between the query embedding and precomputed faq embeddings.
"""

import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "faq", "faq_embeddings.npy")
FAQ_STORE_PATH = os.path.join(BASE_DIR, "faq", "faq_store.json")

MODEL_NAME = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.35
TOP_K = 2


class FAQRetriever:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.embeddings = np.load(EMBEDDINGS_PATH)
        with open(FAQ_STORE_PATH, "r", encoding="utf-8") as f:
            self.faqs = json.load(f)

    def retrieve(self, query, context=""):
        full_query = f"{context} {query}".strip() if context else query
        query_embedding = self.model.encode([full_query], normalize_embeddings=True)[0]

        scores = np.dot(self.embeddings, query_embedding)
        top_indices = np.argsort(scores)[::-1][:TOP_K]

        matches = []
        for idx in top_indices:
            score = float(scores[idx])
            if score < SIMILARITY_THRESHOLD:
                continue
            faq = self.faqs[idx]
            matches.append({
                "question": faq["question"],
                "answer": faq["answer"],
                "score": round(score, 4),
            })

        return {
            "query_used": full_query,
            "matches": matches,
        }
