"""
DataLoader implementations for section 03.

A DataLoader:
  1. Collects all load(key) calls made during a single request tick
  2. Calls the batch function ONCE with all collected keys
  3. Returns each result to the original caller

This collapses N individual DB queries into 1 batch query.
"""

from strawberry.dataloader import DataLoader
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import data_03 as db


async def batch_load_authors(keys: list[str]) -> list[dict | None]:
    """
    Called by the DataLoader with all author IDs requested in this tick.

    Contract:
      - Input:  list of keys in ANY order
      - Output: list of values in THE SAME ORDER as the input keys
                (None for keys that were not found)

    This is important: DataLoader matches results to callers by position.
    If you return results in a different order, callers get wrong data.
    """
    return db.get_authors_by_ids(keys)


def make_author_loader() -> DataLoader:
    """
    Create a fresh DataLoader instance per request.

    DataLoaders must be per-request, not singletons. They cache within
    a request to avoid loading the same ID twice, but that cache must
    be cleared between requests to avoid serving stale data.
    """
    return DataLoader(load_fn=batch_load_authors)
