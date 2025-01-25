import os
import json
from typing import Dict, Any

CACHE_FILEPATH = "data_cache.json"

def load_cache() -> Dict[str, Any]:
    """
    Load the JSON cache from disk. If file doesn't exist, return empty.
    """
    if not os.path.exists(CACHE_FILEPATH):
        return {"hackathons": {}, "locations": {}}

    with open(CACHE_FILEPATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Ensure we have both sub-dicts
        data.setdefault("hackathons", {})
        data.setdefault("locations", {})
        return data

def save_cache(cache_data: Dict[str, Any]) -> None:
    """
    Save the given dictionary to JSON on disk.
    """
    with open(CACHE_FILEPATH, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)