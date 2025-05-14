from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple

class SimilaritySearch:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name, trust_remote_code=True)

    def get_embedding(self, texts: List[str]) -> np.ndarray:
        try:
            embeddings = self.model.encode(texts, task="text-matching")
            return np.array(embeddings)
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return np.empty((0, 0))

    def calculate_scores(self, query: str, documents: List[str]) -> np.ndarray:
        try:
            query_emb = self.get_embedding([query])           
            doc_embs = self.get_embedding(documents)         

            if query_emb.size == 0 or doc_embs.size == 0:
                return np.array([])

            scores = cosine_similarity(doc_embs, query_emb).flatten()
            return scores
        except Exception as e:
            print(f"Error calculating scores: {e}")
            return np.array([])

    def rerank(self,query: str, documents: List[str], top_k: int) -> Tuple[List[int], List[float]]:

        scores = self.calculate_scores(query, documents)
        if scores.size == 0:
            return [], []

        top_k = min(top_k, len(scores))
        sorted_indices = np.argsort(scores)[::-1][:top_k]
        top_scores = [float(scores[i]) for i in sorted_indices]
        return sorted_indices.tolist(), top_scores

    def get_retrieved_documents(self, query: str, documents: List[str], top_k: int) -> List[Tuple[str, float]]:
        indices, scores = self.rerank(query, documents, top_k)
        return [(documents[i], scores[j]) for j, i in enumerate(indices)]

# if __name__ == "__main__":
#     similarity_search = SimilaritySearch("jinaai/jina-embeddings-v3")

#     documents = [
#         "The quick brown fox jumps over the lazy dog.",
#         "A fast auburn fox leaps over a sleepy canine.",
#         "An unrelated sentence about machine learning and AI.",
#         "Another document discussing Python programming."
#     ]
#     query = "fox jumping over dog"
#     top_k = 2

#     results = similarity_search.get_retrieved_documents(query, documents, top_k)


#     for doc, score in results:
#         print(f"Document: {doc}\nScore: {score:.4f}\n")
