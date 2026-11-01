from pathlib import Path

MEMORY_FILE = Path("memory/high_priority.json")

def store_high_priority(record: dict):
    """
    Memory disabled for Phase 4+.
    Intentionally a no-op.
    """
    return
