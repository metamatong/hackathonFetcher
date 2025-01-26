import json
import os
import logging

# Configure logger
logger = logging.getLogger(__name__)

CACHE_FILE = os.getenv("CACHE_FILE", "cache.json")

def load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        logger.info(f"Cache file '{CACHE_FILE}' not found. Initializing empty cache.")
        return {"hackathons": {}, "locations": {}}
    try:
        with open(CACHE_FILE, "r") as f:
            cache_data = json.load(f)
            logger.debug(f"Cache loaded from '{CACHE_FILE}'.")
            return cache_data
    except Exception as e:
        logger.error(f"Error loading cache file '{CACHE_FILE}': {e}", exc_info=True)
        return {"hackathons": {}, "locations": {}}

def save_cache(cache_data: dict):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=4)
            logger.debug(f"Cache saved to '{CACHE_FILE}'.")
    except Exception as e:
        logger.error(f"Error saving cache to '{CACHE_FILE}': {e}", exc_info=True)
