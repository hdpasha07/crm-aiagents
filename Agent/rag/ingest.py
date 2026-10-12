import sys
import argparse
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from .config import BASE_DIR, CHROMA_COLLECTION_NAME
from .vector_store import VectorStoreManager


def ingest_knowledge_base(
    policy_dir: Optional[Path | str] = None,
    file_path: Optional[Path | str] = None,
    reset_collection: bool = False
) -> int:
    """
    Ingests policy documents into the persistent ChromaDB collection.
    
    Args:
        policy_dir: Path to directory containing policy files.
        file_path: Optional single file to ingest.
        reset_collection: If True, clears existing vector store records first.
        
    Returns:
        Total number of chunks in the collection after ingestion.
    """
    print("\n" + "=" * 60)
    print("🚀 ENTERPRISE RAG INGESTION PIPELINE: CHROMADB & GEMINI")
    print("=" * 60)

    vector_store = VectorStoreManager()

    if reset_collection:
        print("🧹 Clearing existing ChromaDB collection...")
        vector_store.clear()
        print("✅ Collection cleared.")

    target_dir = Path(policy_dir or (BASE_DIR / "Agent" / "policies")).resolve()

    if file_path:
        target_file = Path(file_path).resolve()
        print(f"📄 Ingesting single document: {target_file.name}")
        chunks_count = vector_store.ingest_file(target_file)
        print(f"✅ Indexed {chunks_count} chunks from {target_file.name}")
    else:
        print(f"📂 Scanning directory: {target_dir}")
        if not target_dir.exists():
            raise FileNotFoundError(f"Policy directory does not exist: {target_dir}")

        summary = vector_store.ingest_directory(target_dir)
        print("\n📊 Ingestion Summary by Document:")
        print("-" * 60)
        total_new_chunks = 0
        for doc_name, count in summary.items():
            if count >= 0:
                print(f"  • {doc_name:<30} -> {count:>3} chunks indexed")
                total_new_chunks += count
            else:
                print(f"  • {doc_name:<30} -> ❌ FAILED")
        print("-" * 60)
        print(f"✨ Total new chunks processed in this run: {total_new_chunks}")

    total_chunks = vector_store.count()
    print(f"📦 ChromaDB Collection ('{vector_store.collection_name}') Total Size: {total_chunks} chunks")
    print("=" * 60 + "\n")
    return total_chunks


def main():
    parser = argparse.ArgumentParser(
        description="Ingest company policies into persistent ChromaDB vector store."
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Path to directory containing policy files (default: Agent/policies)"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to an individual file to ingest"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear existing collection before ingestion"
    )

    args = parser.parse_args()

    try:
        ingest_knowledge_base(
            policy_dir=args.dir,
            file_path=args.file,
            reset_collection=args.reset
        )
    except Exception as e:
        print(f"❌ Ingestion Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
