"""
Stage 1 of the Builder pipeline: find and load fixture entity files.

Deliberately dumb: no validation happens here. Loading is separated from
validation so later stages can be tested against arbitrary in-memory or
temp-directory fixtures without touching data/curated/.
"""
import json
from pathlib import Path
from typing import List, Tuple


def find_entity_paths(data_dir: Path) -> List[Path]:
    """
    Sorted by filename, purely so error messages and iteration order are
    stable while loading. This is NOT what makes the build artifact
    deterministic -- entities are re-sorted by id before being written
    (see build.py); this sort only avoids depending on directory-listing
    order at this stage too.
    """
    return sorted(Path(data_dir).glob("*.json"))


def load_entities(paths: List[Path]) -> List[Tuple[Path, dict]]:
    loaded = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        loaded.append((path, data))
    return loaded
