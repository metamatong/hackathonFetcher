import os
import re
from typing import List, Dict

import requests
from dotenv import load_dotenv

from utils import is_in_british_columbia_google

# Load environment variables from .env file
load_dotenv()

# Retrieve the API key
GOOGLE_API_MAPS_KEY = os.getenv("GOOGLE_API_MAPS_KEY")

def fetch_hackathon_data(api_url: str) -> List[Dict]:
    """
    Fetches hackathon data from Devpost's API endpoint, returning only
    hackathons that match certain filters:

      - upcoming + recently added (via query params),
      - located in Vancouver/BC/Online,
      - awarding USD or CAD only (exclude hackathons with INR/₹, etc.).

    Args:
        api_url (str): The base Devpost API URL, e.g. "https://devpost.com/api/hackathons"
                       (can include query params like ?order_by=..., &status[]=..., &page=...).

    Returns:
        List[Dict]: A list of dictionaries containing filtered hackathon information.
    """

    # Typically, we still control these query params:
    params = {
        "order_by": "recently-added",
        "status[]": "upcoming",
        "page": 1,
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Raises HTTPError for non-200 statuses
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return []

    data = response.json()
    # Example: Print the raw data to see structure
    # print(data)

    # According to the data snippet, hackathons are in data["hackathons"]
    hackathon_list = data.get("hackathons", [])

    filtered_hackathons = []

    for hackathon in hackathon_list:
        name = hackathon.get("title", "N/A")
        url = hackathon.get("url", "N/A")

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
        # If it's "online" anywhere in the location text, keep it
        if "online" in loc_lower:
            # keep
            pass
        else:
            # else we must confirm geocoding => BC, Canada
            if not is_in_british_columbia_google(location, GOOGLE_API_MAPS_KEY):
                continue  # skip if not in BC

        # If it passes the filters, add it to the final results
        filtered_hackathons.append({
            "name": name,
            "url": url,
            "location": location,
            "prize": prize_num,
            "date": date_text
        })

    return filtered_hackathons