import os
import re
from typing import List, Dict
import requests
from dotenv import load_dotenv

from utils import is_in_british_columbia_google
from cache import load_cache, save_cache

load_dotenv()
GOOGLE_API_MAPS_KEY = os.getenv("GOOGLE_API_MAPS_KEY")


def fetch_hackathon_data(api_url: str) -> List[Dict]:
    """
    Fetches hackathon data from Devpost's API endpoint, returning only hackathons
    that match certain filters:
      - upcoming + recently added,
      - located in Vancouver/BC/Online,
      - awarding USD or CAD only (exclude hackathons with INR/₹, etc.).
    """
    # Control query params
    params = {
        "order_by": "recently-added",
        "status[]": "upcoming",
        "page": 1,
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return []

    data = response.json()
    hackathon_list = data.get("hackathons", [])

    # === Load cache (for hackathons & locations) ===
    cache_data = load_cache()
    hackathon_cache = cache_data["hackathons"]  # e.g. { "https://devpost.com/hackathons/XYZ": {...} }

    filtered_hackathons = []

    for hackathon in hackathon_list:
        name = hackathon.get("title", "N/A")
        url = hackathon.get("url", "N/A")

        # If we've already seen this hackathon in cache, skip the heavy checks
        # Or decide if you want to re-check location. For demonstration, we’ll skip if in cache.
        if url in hackathon_cache:
            # Optionally, we can re-add it to filtered results if it was valid
            filtered_hackathons.append(hackathon_cache[url])
            continue

        loc_dict = hackathon.get("displayed_location", {})
        location = loc_dict.get("location", "Unknown")

        prize_text = hackathon.get("prize_amount", "")
        prize_match = re.search(r'[\d,]+', prize_text)
        prize_num = prize_match.group(0).replace(",", "") if prize_match else "0"

        date_text = hackathon.get("submission_period_dates", "Unknown")

        # skip if the prize text includes currencies we exclude
        if any(x in prize_text for x in ["₹", "INR", "£"]):
            continue

        # location check:
        loc_lower = location.lower()
        if "online" in loc_lower:
            # keep
            pass
        else:
            # else we must confirm geocoding => BC, Canada
            if not is_in_british_columbia_google(location, GOOGLE_API_MAPS_KEY):
                continue  # skip if not in BC

        # If it passes the filters, construct the dictionary
        hackathon_dict = {
            "name": name,
            "url": url,
            "location": location,
            "prize": prize_num,
            "date": date_text
        }

        # Save to the hackathon cache
        hackathon_cache[url] = hackathon_dict

        filtered_hackathons.append(hackathon_dict)

    # Persist the updated cache
    save_cache(cache_data)

    return filtered_hackathons