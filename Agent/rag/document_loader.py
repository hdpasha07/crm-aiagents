import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from .schemas import DocumentChunk
from .config import CHUNK_SIZE, CHUNK_OVERLAP

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


def clean_text(text: str) -> str:
    """Normalize whitespace and strip non-printable characters."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple blank lines down to two
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_title(text: str, default: str) -> str:
    """Extract first markdown heading (# Title) or fall back to default."""
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return default


def load_file_content(file_path: Path) -> List[Dict[str, Any]]:
    """
    Loads text content and raw metadata from a single file.
    Returns a list of dicts: [{"text": str, "metadata": dict}]
    (For PDFs, one entry per page is generated).
    """
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = file_path.suffix.lower()
    results = []

    if ext in [".md", ".markdown", ".txt"]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()
        cleaned = clean_text(raw_text)
        title = extract_title(cleaned, file_path.stem.replace("_", " ").title())
        results.append({
            "text": cleaned,
            "metadata": {
                "source": file_path.name,
                "file_path": str(file_path),
                "extension": ext,
                "title": title
            }
        })

    elif ext == ".json":
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        # Format JSON into readable key-value documentation
        formatted_text = json.dumps(data, indent=2)
        results.append({
            "text": formatted_text,
            "metadata": {
                "source": file_path.name,
                "file_path": str(file_path),
                "extension": ext,
                "title": file_path.stem.replace("_", " ").title()
            }
        })

    elif ext == ".pdf":
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf is required to load PDF documents. Install via `pip install pypdf`.")
        reader = PdfReader(str(file_path))
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            cleaned = clean_text(page_text)
            if cleaned:
                results.append({
                    "text": cleaned,
                    "metadata": {
                        "source": file_path.name,
                        "file_path": str(file_path),
                        "extension": ext,
                        "title": f"{file_path.stem} (Page {page_idx + 1})",
                        "page": page_idx + 1,
                        "total_pages": len(reader.pages)
                    }
                })

    else:
        raise ValueError(f"Unsupported file extension: {ext}. Supported: .md, .txt, .json, .pdf")

    return results


def split_text_into_chunks(
    text: str,
    base_metadata: Dict[str, Any],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP
) -> List[DocumentChunk]:
    """
    Splits text recursively using paragraphs, sentences, and words.
    Preserves document metadata and tags each chunk with unique id and chunk_index.
    """
    if not text.strip():
        return []

    # If text is already smaller than chunk_size, return single chunk
    if len(text) <= chunk_size:
        doc_source = base_metadata.get("source", "doc")
        chunk_id = f"{doc_source}_chunk_0"
        meta = {**base_metadata, "chunk_index": 0, "char_count": len(text)}
        return [DocumentChunk(id=chunk_id, content=text, metadata=meta)]

    # Recursive split separators
    separators = ["\n\n", "\n", ". ", " ", ""]

    def _split_recursive(t: str, seps: List[str]) -> List[str]:
        if not seps:
            return [t[i : i + chunk_size] for i in range(0, len(t), chunk_size - chunk_overlap)]
        
        sep = seps[0]
        remaining_seps = seps[1:]
        
        parts = t.split(sep) if sep else list(t)
        chunks: List[str] = []
        current = ""

        for part in parts:
            candidate = f"{current}{sep}{part}" if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current.strip())
                if len(part) > chunk_size:
                    # Part itself exceeds chunk_size, recurse on finer separator
                    sub_chunks = _split_recursive(part, remaining_seps)
                    chunks.extend(sub_chunks)
                    current = ""
                else:
                    current = part

        if current and current.strip():
            chunks.append(current.strip())

        return chunks

    raw_chunks = _split_recursive(text, separators)

    # Post-process with overlap window if needed
    final_chunks: List[DocumentChunk] = []
    doc_source = base_metadata.get("source", "doc")

    for idx, c in enumerate(raw_chunks):
        c_clean = c.strip()
        if not c_clean:
            continue
        chunk_id = f"{doc_source}_chunk_{idx}"
        chunk_meta = {
            **base_metadata,
            "chunk_index": idx,
            "char_count": len(c_clean)
        }
        final_chunks.append(
            DocumentChunk(id=chunk_id, content=c_clean, metadata=chunk_meta)
        )

    return final_chunks


def load_and_chunk_file(
    file_path: Path | str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP
) -> List[DocumentChunk]:
    """High-level utility to load a file and return split DocumentChunks."""
    path = Path(file_path).resolve()
    sections = load_file_content(path)
    all_chunks = []
    for section in sections:
        chunks = split_text_into_chunks(
            text=section["text"],
            base_metadata=section["metadata"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        all_chunks.extend(chunks)
    return all_chunks

