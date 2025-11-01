import math
from typing import List

import torch
from sentence_transformers import SentenceTransformer


def l2_normalize(vec: List[float]) -> List[float]:
    mag_sq = 0.0
    for x in vec:
        mag_sq += x * x
    if mag_sq == 0.0:
        return vec
    mag = math.sqrt(mag_sq)
    return [x / mag for x in vec]


class EmbeddingModel:
    def __init__(self, device: str | None = None):
        # pick device automatically
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = device
        self.model = SentenceTransformer(
            "BAAI/bge-small-en-v1.5",
            device=self.device,
        )

    def embed(self, text: str) -> List[float]:
        with torch.no_grad():
            emb = self.model.encode(
                [text],
                convert_to_tensor=True,
                normalize_embeddings=True,
            )
        # emb shape: [1, dim]
        return emb[0].tolist()


def dot_sim(a: List[float], b: List[float]) -> float:
    # store normalized vectors, dot product == cosine similarity
    total = 0.0
    for x, y in zip(a, b):
        total += x * y
    return total


def get_embedding_model(device: str | None = None) -> EmbeddingModel:
    """Convenience function to get an initialized embedding model."""
    return EmbeddingModel(device=device)


if __name__ == "__main__":
    # Test basic embedding functionality
    embed_model = EmbeddingModel()

    print("Testing embedding similarity...")
    # Test embedding similarity
    vec1 = embed_model.embed("steal the ledger")
    vec2 = embed_model.embed("take the book")
    vec3 = embed_model.embed("cook dinner")

    sim12 = dot_sim(vec1, vec2)
    sim13 = dot_sim(vec1, vec3)

    print(f"Similarity between 'steal the ledger' and 'take the book': {sim12:.3f}")
    print(f"Similarity between 'steal the ledger' and 'cook dinner': {sim13:.3f}")

    print("\nEmbedding tests completed!")
