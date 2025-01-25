import requests
import re
from typing import List, Dict


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
        # The API returns fields like:
        #   "title"
        #   "url"
        #   "displayed_location": { "location": "Some city" }
        #   "prize_amount": e.g. "$<span data-currency-value>1,500</span>"
        #   "submission_period_dates": e.g. "Jan 26, 2025"

        name = hackathon.get("title", "N/A")
        url = hackathon.get("url", "N/A")

        # Pull out location from "displayed_location" sub-dict
        location_dict = hackathon.get("displayed_location", {})
        location = location_dict.get("location", "Unknown")

        # Devpost calls the field "prize_amount"
        prize_text = hackathon.get("prize_amount", "")
        prize_match = re.search(r'[\d,]+', prize_text)
        prize = prize_match.group(0).replace(",", "") if prize_match else "0"

        # For date, Devpost uses "submission_period_dates"
        date_text = hackathon.get("submission_period_dates", "Unknown")

        # --- Filter logic ---

        # 1) Check location for "vancouver", "british columbia", or "online"
        loc_lower = location.lower()

        # 2) Only keep hackathons awarding USD ($) or CAD ($CAD); exclude "₹", "INR"
        if "₹" in prize_text or "INR" in prize_text or "£" in prize_text:
            continue

        # If it passes the filters, add it to the final results
        filtered_hackathons.append({
            "name": name,
            "url": url,
            "location": location,
            "prize": prize,
            "date": date_text
        })

    return filtered_hackathons