"""
Embeds FAQ questions with sentence-transformers and saves the
embeddings and faq data to disk for fast loading at query time.
"""

import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAQ_PATH = os.path.join(BASE_DIR, "data", "faqs.json")
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "faq", "faq_embeddings.npy")
FAQ_STORE_PATH = os.path.join(BASE_DIR, "faq", "faq_store.json")

MODEL_NAME = "all-MiniLM-L6-v2"


def build_index():
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        faqs = json.load(f)

    model = SentenceTransformer(MODEL_NAME)
    questions = [f["question"] for f in faqs]
    embeddings = model.encode(questions, normalize_embeddings=True)

    np.save(EMBEDDINGS_PATH, embeddings)

    with open(FAQ_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(faqs, f, indent=2, ensure_ascii=False)

    print(f"indexed {len(faqs)} faqs")


if __name__ == "__main__":
    build_index()
