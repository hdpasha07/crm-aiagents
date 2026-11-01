from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Represents an indexed or retrieved text chunk with metadata."""
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    distance: Optional[float] = None
    relevance_score: Optional[float] = None


class Citation(BaseModel):
    """Represents a grounded reference source cited in the LLM response."""
    source: str
    chunk_id: Optional[str] = None
    snippet: Optional[str] = None


class RAGResponse(BaseModel):
    """Structured response returned by the Gemini RAG pipeline."""
    query: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    context_chunks: List[DocumentChunk] = Field(default_factory=list)
    model: str
    grounded: bool = True

