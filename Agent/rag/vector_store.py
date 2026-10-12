import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from .config import (
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_RESULTS,
    RELEVANCE_THRESHOLD
)
from .schemas import DocumentChunk
from .embeddings import GeminiEmbeddingFunction
from .document_loader import load_and_chunk_file


class VectorStoreManager:
    """
    Persistent ChromaDB vector store wrapper for enterprise knowledge ingestion
    and similarity retrieval with normalized relevance scores.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_function: Optional[Any] = None
    ):
        self.persist_directory = Path(persist_directory or CHROMA_PERSIST_DIR).resolve()
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name or CHROMA_COLLECTION_NAME

        # Initialize Gemini embedding function if not provided
        self.embedding_function = embedding_function or GeminiEmbeddingFunction()

        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection configured with cosine distance metric
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

    def ingest_chunks(self, chunks: List[DocumentChunk]) -> int:
        """
        Upserts a list of DocumentChunks into the persistent collection.
        
        Args:
            chunks: List of DocumentChunk models.
            
        Returns:
            Number of chunks successfully upserted.
        """
        if not chunks:
            return 0

        ids = [c.id for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [c.metadata for c in chunks]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        return len(chunks)

    def ingest_file(
        self,
        file_path: Path | str,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP
    ) -> int:
        """
        Loads, chunks, and indexes a single document or PDF into ChromaDB.
        
        Args:
            file_path: Path to target file.
            chunk_size: Target character count per chunk.
            chunk_overlap: Character overlap between consecutive chunks.
            
        Returns:
            Count of indexed chunks.
        """
        chunks = load_and_chunk_file(
            file_path=file_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return self.ingest_chunks(chunks)

    def ingest_directory(
        self,
        dir_path: Path | str,
        extensions: Optional[List[str]] = None,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP
    ) -> Dict[str, int]:
        """
        Scans a directory for supported files and ingests them into ChromaDB.
        
        Args:
            dir_path: Directory path containing policy documents.
            extensions: Allowed extensions (defaults to .md, .txt, .json, .pdf).
            chunk_size: Character count per chunk.
            chunk_overlap: Overlap character count.
            
        Returns:
            Dictionary mapping filename to indexed chunk count.
        """
        dir_path = Path(dir_path).resolve()
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Directory not found: {dir_path}")

        allowed_exts = set(extensions or [".md", ".markdown", ".txt", ".json", ".pdf"])
        summary = {}

        for item in sorted(dir_path.iterdir()):
            if item.is_file() and item.suffix.lower() in allowed_exts:
                try:
                    count = self.ingest_file(item, chunk_size, chunk_overlap)
                    summary[item.name] = count
                except Exception as e:
                    summary[item.name] = -1
                    print(f"⚠️ Failed to ingest {item.name}: {e}")

        return summary

    def similarity_search(
        self,
        query: str,
        top_k: int = TOP_K_RESULTS,
        relevance_threshold: Optional[float] = None
    ) -> List[DocumentChunk]:
        """
        Performs semantic similarity search with cosine relevance scoring.
        
        Args:
            query: The customer support query or text.
            top_k: Number of nearest chunks to retrieve.
            relevance_threshold: Minimum acceptable relevance score [0.0 - 1.0].
            
        Returns:
            List of matching DocumentChunk instances sorted by descending relevance.
        """
        if not query.strip():
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        matched_chunks: List[DocumentChunk] = []

        ids_list = results.get("ids", [[]])[0]
        docs_list = results.get("documents", [[]])[0]
        meta_list = results.get("metadatas", [[]])[0]
        dist_list = results.get("distances", [[]])[0]

        for chunk_id, content, meta, dist in zip(ids_list, docs_list, meta_list, dist_list):
            # For cosine distance (range [0, 2]), similarity = 1.0 - distance
            # Clamped to [0.0, 1.0]
            relevance = max(0.0, min(1.0, 1.0 - float(dist)))

            threshold = relevance_threshold if relevance_threshold is not None else RELEVANCE_THRESHOLD
            if relevance >= threshold:
                matched_chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        content=content,
                        metadata=meta or {},
                        distance=float(dist),
                        relevance_score=round(relevance, 4)
                    )
                )

        return matched_chunks

    def count(self) -> int:
        """Returns the total number of chunks currently in the vector store."""
        return self.collection.count()

    def clear(self) -> None:
        """Deletes all records and resets the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

    # ── User Specific Workarounds (Continuous Episodic Memory) ─────────────────

    def get_user_workarounds_collection(self):
        """Returns or creates the dedicated ChromaDB collection for user workarounds."""
        return self.client.get_or_create_collection(
            name="user_specific_workarounds",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

    def store_user_workaround(
        self,
        user_id: str,
        issue_summary: str,
        successful_solution: str,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Embed and persist a verified user-specific workaround into ChromaDB.
        
        Args:
            user_id: Unique customer ID.
            issue_summary: Brief description of the reported problem.
            successful_solution: The confirmed solution steps that fixed the issue.
            extra_metadata: Optional dictionary of additional metadata tags.
            
        Returns:
            The unique document ID generated for the stored workaround.
        """
        collection = self.get_user_workarounds_collection()
        doc_id = f"workaround_{user_id}_{int(time.time() * 1000)}"
        now_iso = datetime.now(timezone.utc).isoformat()

        content = (
            f"User Problem: {issue_summary.strip()}\n"
            f"Successful Workaround / Solution: {successful_solution.strip()}"
        )

        metadata = {
            "user_id": str(user_id),
            "issue_summary": str(issue_summary).strip()[:200],
            "timestamp": now_iso,
        }
        if extra_metadata:
            for k, v in extra_metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    metadata[k] = v

        collection.upsert(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata]
        )
        return doc_id

    def query_user_workarounds(
        self,
        query: str,
        user_id: Optional[str] = None,
        top_k: int = 3,
        relevance_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Semantically search past successful workarounds stored in ChromaDB.
        Filters by user_id if specified.
        """
        if not query.strip():
            return []

        collection = self.get_user_workarounds_collection()
        where_filter = {"user_id": str(user_id)} if user_id else None

        query_kwargs = {
            "query_texts": [query],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        try:
            results = collection.query(**query_kwargs)
        except Exception as e:
            print(f"⚠️ Error querying user workarounds: {e}")
            return []

        ids_list = results.get("ids", [[]])[0]
        docs_list = results.get("documents", [[]])[0]
        meta_list = results.get("metadatas", [[]])[0]
        dist_list = results.get("distances", [[]])[0]

        matches: List[Dict[str, Any]] = []
        for chunk_id, content, meta, dist in zip(ids_list, docs_list, meta_list, dist_list):
            relevance = max(0.0, min(1.0, 1.0 - float(dist)))
            if relevance >= relevance_threshold:
                matches.append({
                    "id": chunk_id,
                    "content": content,
                    "metadata": meta or {},
                    "relevance_score": round(relevance, 4),
                    "user_id": (meta or {}).get("user_id"),
                })

        return matches

