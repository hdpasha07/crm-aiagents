import sys
from pathlib import Path

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from Agent.rag.vector_store import VectorStoreManager
from Agent.rag.llm_rag import GeminiRAG
from Agent.rag.ingest import ingest_knowledge_base
from Agent.rag.config import BASE_DIR


def run_rag_verification():
    print("\n" + "=" * 70)
    print("[TEST] STARTING ENTERPRISE RAG VERIFICATION (CHROMADB + GEMINI API)")
    print("=" * 70)

    # 1. Ingest sample policies into ChromaDB
    print("\n[Step 1] Ingesting knowledge base policies into ChromaDB...")
    policies_dir = BASE_DIR / "Agent" / "policies"
    total_chunks = ingest_knowledge_base(policy_dir=policies_dir, reset_collection=True)
    assert total_chunks > 0, f"Expected chunks > 0, but got {total_chunks}"
    print(f"[OK] Ingestion successful: {total_chunks} chunks stored.")

    # 2. Test Similarity Search & Relevance Scores
    print("\n[Step 2] Testing Semantic Similarity Search with Relevance Scores...")
    vector_store = VectorStoreManager()
    test_query = "What is the deadline for requesting a refund and who pays shipping?"
    retrieved = vector_store.similarity_search(test_query, top_k=3)

    assert len(retrieved) > 0, "No chunks retrieved from similarity search!"
    print(f"Query: '{test_query}'")
    print(f"Retrieved {len(retrieved)} relevant chunks:")
    for i, chunk in enumerate(retrieved, 1):
        print(f"  {i}. Chunk ID: {chunk.id}")
        print(f"     Source: {chunk.metadata.get('source')} | Title: {chunk.metadata.get('title')}")
        print(f"     Relevance Score: {chunk.relevance_score} (Cosine Distance: {chunk.distance:.4f})")
        print(f"     Preview: {chunk.content[:100]}...\n")

    # 3. Test Grounded Gemini RAG Generation
    print("\n[Step 3] Testing Grounded Gemini LLM Generation with Citations...")
    rag_engine = GeminiRAG(vector_store=vector_store)

    test_queries = [
        "What is the return window and what happens if I return an opened intimate item?",
        "How many business days of tracking inactivity before a package is declared lost?",
        "Can I pay using Bitcoin or cash on delivery?"
    ]

    for idx, q in enumerate(test_queries, 1):
        print(f"\n--- [Scenario {idx}] Customer Query: \"{q}\" ---")
        rag_response = rag_engine.generate_grounded_response(q, top_k=3)

        print("\n[Gemini Grounded Answer]:")
        print(rag_response.answer)

        print("\n[Extracted Citations]:")
        if rag_response.citations:
            for cit in rag_response.citations:
                print(f"  * Source: {cit.source} (Chunk: {cit.chunk_id or 'N/A'})")
        else:
            print("  (No direct citations extracted)")

        print(f"\nVerified Grounded: {rag_response.grounded}")
        assert rag_response.answer.strip(), f"Empty answer generated for scenario {idx}"

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL PHASE 1 RAG TESTS PASSED SUCCESSFULLY WITH ZERO ERRORS!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        run_rag_verification()
    except Exception as e:
        print(f"\n[ERROR] Verification failed with error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

