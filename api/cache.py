# cache.py

import os
import redis
import json
import logging

logger = logging.getLogger(__name__)

# Get the Upstash Redis URL from environment variables
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
if not UPSTASH_REDIS_URL:
    logger.error("UPSTASH_REDIS_URL environment variable not set.")
    raise Exception("UPSTASH_REDIS_URL not set.")

# Create a Redis client instance.
# decode_responses=True tells the client to return Python strings (not bytes)
redis_client = redis.from_url(UPSTASH_REDIS_URL, decode_responses=True)


def load_cache() -> dict:
    """
    Loads cached data for hackathons and locations from Redis.
    If a key is missing, returns an empty dict for that cache.
    """
    hackathons = redis_client.get("cache:hackathons")
    locations = redis_client.get("cache:locations")

    if hackathons:
        try:
            hackathons = json.loads(hackathons)
        except Exception as e:
            logger.error(f"Error decoding hackathons cache: {e}")
            hackathons = {}
    else:
        hackathons = {}

    if locations:
        try:
            locations = json.loads(locations)
        except Exception as e:
            logger.error(f"Error decoding locations cache: {e}")
            locations = {}
    else:
        locations = {}

    return {"hackathons": hackathons, "locations": locations}


def save_cache(cache_data: dict):
    """
    Saves the cache data (for hackathons and locations) to Redis.
    You can also add an expiration time (in seconds) if desired by passing the `ex` parameter.
    """
    hackathons = json.dumps(cache_data.get("hackathons", {}))
    locations = json.dumps(cache_data.get("locations", {}))

    redis_client.set("cache:hackathons", hackathons, ex=604800)
    redis_client.set("cache:locations", locations, ex=604800)