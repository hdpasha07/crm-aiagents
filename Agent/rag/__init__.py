"""
Enterprise Customer Support Agent - Modular RAG Subsystem
Powered by ChromaDB Vector Store & Google Gemini API
"""

from .config import (
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME,
    GEMINI_MODEL,
    GEMINI_EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_RESULTS
)
from .schemas import DocumentChunk, Citation, RAGResponse
from .embeddings import GeminiEmbeddingFunction
from .document_loader import load_and_chunk_file, split_text_into_chunks
from .vector_store import VectorStoreManager
from .llm_rag import GeminiRAG
from .ingest import ingest_knowledge_base

__all__ = [
    "CHROMA_PERSIST_DIR",
    "CHROMA_COLLECTION_NAME",
    "GEMINI_MODEL",
    "GEMINI_EMBEDDING_MODEL",
    "CHUNK_SIZE",
    "CHUNK_OVERLAP",
    "TOP_K_RESULTS",
    "DocumentChunk",
    "Citation",
    "RAGResponse",
    "GeminiEmbeddingFunction",
    "load_and_chunk_file",
    "split_text_into_chunks",
    "VectorStoreManager",
    "GeminiRAG",
    "ingest_knowledge_base"
]

