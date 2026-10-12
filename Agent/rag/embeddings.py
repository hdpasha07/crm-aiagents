import os
from typing import List, Optional
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from google import genai
from .config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL


class GeminiEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    ChromaDB compatible Embedding Function powered by Google Gemini API.
    Uses 'gemini-embedding-001' (or configured model) for semantic vector representations.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = GEMINI_EMBEDDING_MODEL,
        batch_size: int = 32
    ):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please ensure it is present in .env or passed to GeminiEmbeddingFunction."
            )
        self.model_name = model_name
        self.batch_size = batch_size
        self._client = genai.Client(api_key=self.api_key)

    def __call__(self, input: Documents) -> Embeddings:
        """
        Computes embeddings for a list of document strings.
        
        Args:
            input: List of text strings to embed.
            
        Returns:
            List of embedding vector floats.
        """
        if not input:
            return []

        embeddings: List[List[float]] = []

        # Process in batches to stay within API payload guidelines
        for i in range(0, len(input), self.batch_size):
            batch = input[i : i + self.batch_size]
            try:
                response = self._client.models.embed_content(
                    model=self.model_name,
                    contents=batch
                )
                if hasattr(response, "embeddings") and response.embeddings:
                    for emb in response.embeddings:
                        embeddings.append(list(emb.values))
                else:
                    raise RuntimeError("Gemini embed_content returned empty embeddings response.")
            except Exception as e:
                raise RuntimeError(
                    f"Error computing Gemini embeddings for batch ({i} to {i + len(batch)}): {e}"
                ) from e

        return embeddings

