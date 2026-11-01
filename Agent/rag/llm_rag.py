import re
from typing import List, Optional
from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_MODEL, TOP_K_RESULTS
from .schemas import RAGResponse, Citation, DocumentChunk
from .vector_store import VectorStoreManager


def strip_source_metadata(text: str) -> str:
    """Strips internal source and chunk metadata brackets from text."""
    if not text:
        return ""
    cleaned = re.sub(r"\[(?:Source|Chunk|Source Document|Chunk ID)[^\]]*\]", "", text)
    cleaned = re.sub(r" +([.,!?;:])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = "\n".join(line.rstrip() for line in cleaned.splitlines())
    return cleaned.strip()


class GeminiRAG:
    """
    Modular RAG Engine combining ChromaDB vector retrieval with Google Gemini LLM
    for generating grounded, cited customer support responses.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStoreManager] = None,
        model_name: str = GEMINI_MODEL,
        api_key: Optional[str] = None
    ):
        self.vector_store = vector_store or VectorStoreManager()
        self.model_name = model_name
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required to initialize GeminiRAG.")
        self.client = genai.Client(api_key=self.api_key)

    def _build_context_prompt(self, chunks: List[DocumentChunk]) -> str:
        """Formats retrieved chunks into clear, cited context blocks."""
        if not chunks:
            return "No relevant policy documents found in knowledge base."

        formatted_blocks = []
        for idx, chunk in enumerate(chunks, 1):
            source = chunk.metadata.get("source", "Policy Document")
            chunk_id = chunk.id
            relevance = chunk.relevance_score if chunk.relevance_score is not None else "N/A"
            block = (
                f"[Source Document: {source} | Chunk ID: {chunk_id} | Relevance: {relevance}]\n"
                f"{chunk.content}"
            )
            formatted_blocks.append(block)

        return "\n\n---\n\n".join(formatted_blocks)

    def _extract_citations(self, text: str, context_chunks: List[DocumentChunk]) -> List[Citation]:
        """
        Extracts citations formatted as [Source: <doc>, Chunk: <id>] from generated answer.
        Falls back to linking retrieved chunks if format varies.
        """
        citations: List[Citation] = []
        seen = set()

        # Regex pattern matching [Source: <doc>, Chunk: <id>] or [Source: <doc>]
        matches = re.findall(r"\[Source:\s*([^,\]]+)(?:,\s*Chunk:\s*([^\]]+))?\]", text)
        for doc_name, chunk_id in matches:
            clean_doc = doc_name.strip()
            clean_chunk = chunk_id.strip() if chunk_id else None
            key = (clean_doc, clean_chunk)
            if key not in seen:
                seen.add(key)
                citations.append(
                    Citation(
                        source=clean_doc,
                        chunk_id=clean_chunk,
                        snippet=f"Referenced from {clean_doc}"
                    )
                )

        # If model did not emit bracket citations but referenced content from chunks, include top chunks
        if not citations and context_chunks:
            for c in context_chunks[:2]:
                src = c.metadata.get("source", "Knowledge Base")
                citations.append(
                    Citation(
                        source=src,
                        chunk_id=c.id,
                        snippet=c.content[:120] + "..." if len(c.content) > 120 else c.content
                    )
                )

        return citations

    def generate_grounded_response(
        self,
        query: str,
        top_k: int = TOP_K_RESULTS,
        relevance_threshold: Optional[float] = None,
        customer_facing: bool = False
    ) -> RAGResponse:
        """
        Performs retrieval from ChromaDB, constructs a grounded context prompt,
        and invokes Gemini to generate an answer with citations.
        
        Args:
            query: The customer support inquiry.
            top_k: Number of policy chunks to retrieve.
            relevance_threshold: Minimum cosine similarity score.
            customer_facing: If True, instructs the LLM not to include internal bracket citations.
            
        Returns:
            Structured RAGResponse containing answer, citations, and context chunks.
        """
        # 1. Retrieve relevant context from ChromaDB
        matched_chunks = self.vector_store.similarity_search(
            query=query,
            top_k=top_k,
            relevance_threshold=relevance_threshold
        )

        context_text = self._build_context_prompt(matched_chunks)

        if customer_facing:
            citation_instructions = (
                "Provide a natural, customer-facing response. "
                "DO NOT append internal source files, chunk metadata, or brackets like [Source: ...] in your final output."
            )
            answer_prefix = "ANSWER:"
        else:
            citation_instructions = (
                "For EVERY claim, rule, SLA, or timeline you mention, you MUST include an inline citation in this exact format:\n"
                "   [Source: <Source Document>, Chunk: <Chunk ID>]"
            )
            answer_prefix = "ANSWER (with inline citations):"

        # 2. Construct grounded prompt with strict instructions
        prompt = f"""You are an Enterprise AI Customer Support Specialist.
Your mission is to provide accurate, empathetic, and professional support answers based STRICTLY on the verified company support policies provided below.

GROUNDING & CITATION RULES:
1. Answer the customer query using ONLY the verified facts from the POLICY CONTEXT below.
2. {citation_instructions}
3. If the context does not contain enough information to answer the inquiry, state clearly:
   "Our verified policies do not contain sufficient information to answer this question. Please allow me to connect you with a human support specialist."
4. Never assume, extrapolate, or invent policies that are not explicitly stated.

--- POLICY CONTEXT ---
{context_text}
--- END POLICY CONTEXT ---

CUSTOMER QUERY:
{query}

{answer_prefix}"""

        # 3. Invoke Google Gemini
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for strict factual grounding
            )
        )

        answer_text = response.text or ""
        citations = self._extract_citations(answer_text, matched_chunks)

        if customer_facing:
            answer_text = strip_source_metadata(answer_text)

        # Determine if answer is grounded or fell back to out-of-scope disclaimer
        is_grounded = "do not contain sufficient information" not in answer_text.lower()

        return RAGResponse(
            query=query,
            answer=answer_text,
            citations=citations,
            context_chunks=matched_chunks,
            model=self.model_name,
            grounded=is_grounded
        )
