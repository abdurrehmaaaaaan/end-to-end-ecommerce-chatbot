"""
Semantic router. Embeds the query and compares it against example
utterances for each route using cosine similarity. No agents or
tool-calling, this is a plain embedding similarity lookup.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

# example utterances per route, used to build route centroids
ROUTE_EXAMPLES = {
    "SQL": [
        "show me laptops under 200000",
        "list hp laptops",
        "cheapest laptop available",
        "laptops with 16gb ram",
        "which dell laptops do you have",
        "laptop with rtx graphics card",
        "show laptops between 150000 and 300000",
        "most expensive laptop you have",
        "laptops with core i7 processor",
        "what brands of laptops are available",
    ],
    "FAQ": [
        "what is your return policy",
        "how long does delivery take",
        "do you offer installment plans",
        "can i pay cash on delivery",
        "how do i claim warranty",
        "can i cancel my order",
        "what is open parcel delivery",
        "how do refunds work",
        "can i pick up my order myself",
        "how do i contact customer support",
    ],
}

# route pairs are only used when scores are close together
CLOSE_SCORE_MARGIN = 0.05


class SemanticRouter:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.route_centroids = {}
        for route, examples in ROUTE_EXAMPLES.items():
            embeddings = self.model.encode(examples, normalize_embeddings=True)
            self.route_centroids[route] = np.mean(embeddings, axis=0)

    def route(self, query, context=""):
        # context prepended for follow up queries, keeps routing aware
        # of the last turn without needing an agent to decide this
        full_query = f"{context} {query}".strip() if context else query
        query_embedding = self.model.encode([full_query], normalize_embeddings=True)[0]

        scores = {}
        for route, centroid in self.route_centroids.items():
            score = float(np.dot(query_embedding, centroid))
            scores[route] = round(score, 4)

        sorted_routes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_route, top_score = sorted_routes[0]
        second_route, second_score = sorted_routes[1]

        if (top_score - second_score) < CLOSE_SCORE_MARGIN:
            decision = "BOTH"
        else:
            decision = top_route

        return {
            "decision": decision,
            "scores": scores,
            "query_used_for_routing": full_query,
        }
