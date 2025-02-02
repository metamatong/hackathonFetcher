import json
import logging
import os

from dotenv import load_dotenv
from upstash_redis import Redis

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Get the Upstash Redis URL from environment variables
CACHE_KV_REST_API_URL = os.getenv("CACHE_KV_REST_API_URL")
CACHE_KV_REST_API_TOKEN = os.getenv("CACHE_KV_REST_API_TOKEN")

if not CACHE_KV_REST_API_URL:
    logger.error("CACHE_KV_REST_API_URL environment variable not set.")
    raise Exception("CACHE_KV_REST_API_URL not set.")

if not CACHE_KV_REST_API_TOKEN:
    logger.error("CACHE_KV_REST_API_TOKEN environment variable not set.")
    raise Exception("CACHE_KV_REST_API_TOKEN not set.")

# Create a Redis client instance.
# decode_responses=True tells the client to return Python strings (not bytes)
redis_client = Redis(url=CACHE_KV_REST_API_URL, token=CACHE_KV_REST_API_TOKEN)


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