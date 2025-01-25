import requests
from cache import load_cache, save_cache

def is_in_british_columbia_google(address: str, api_key: str) -> bool:
    # 1. Load current cache
    cache_data = load_cache()
    location_cache = cache_data["locations"]  # e.g., {"Vancouver, BC": True, "Berlin, Germany": False}

    # 2. Check if we already have a cached result
    if address in location_cache:
        return location_cache[address]

    # 3. If not cached, we call the Google Geocoding API
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()

    # If no results, we consider it not in BC
    if not data.get("results"):
        location_cache[address] = False
        save_cache(cache_data)
        return False

    # The first result
    result = data["results"][0]

    # parse address_components
    is_bc = True  # We'll assume True until proven otherwise
    for component in result["address_components"]:
        if "administrative_area_level_1" in component["types"]:
            province = component["long_name"].lower()
            if province != "british columbia":
                is_bc = False
                break
        if "country" in component["types"]:
            country = component["short_name"].lower()
            if country != "ca":
                is_bc = False
                break

    # 4. Save the result to the cache
    location_cache[address] = is_bc
    save_cache(cache_data)

    return is_bc