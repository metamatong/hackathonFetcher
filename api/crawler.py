import logging
import os
import re
from typing import List, Dict
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup  # For parsing HTML content

from .utils import is_in_british_columbia_google
from .cache import load_cache, save_cache

load_dotenv()
GOOGLE_API_MAPS_KEY = os.getenv("GOOGLE_API_MAPS_KEY")

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_hackathon_data(api_url: str) -> List[Dict]:
    """
    Fetches hackathon data from Devpost's API endpoint, returning only hackathons
    that match certain filters:
      - Upcoming + recently added
      - Located in Vancouver/BC/Online
      - Awarding USD or CAD only (exclude hackathons with INR/₹, GBP/£, etc.)
      - Prize amount greater than zero
    """
    # Control query params
    params = {
        "order_by": "recently-added",
        "status[]": "upcoming",
        "page": 1,
    }

    try:
        logger.debug(f"Making GET request to {api_url} with params {params}")
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        logger.debug("API request successful.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from API: {e}", exc_info=True)
        return []

    try:
        data = response.json()
        hackathon_list = data.get("hackathons", [])
        logger.debug(f"Received {len(hackathon_list)} hackathons from API.")
    except ValueError as e:
        logger.error(f"Error parsing JSON response: {e}", exc_info=True)
        return []

    # === Load cache (for hackathons & locations) ===
    cache_data = load_cache()
    hackathon_cache = cache_data.get("hackathons", {})  # Safely get "hackathons" key

    filtered_hackathons = []

    # Define currency symbol to code mapping
    symbol_to_currency = {
        '$': 'USD',
        'CAD': 'CAD',  # Assuming 'CAD' might appear as 'CAD' in prize_text
        # Add more mappings if needed
    }

    for hackathon in hackathon_list:
        title = hackathon.get("title", "N/A")
        url = hackathon.get("url", "N/A")

        # **Skip hackathons already in cache**
        if url in hackathon_cache:
            logger.debug(f"Skipping hackathon '{title}' as it is already in cache.")
            continue  # Skip to the next hackathon

        displayed_location = hackathon.get("displayed_location", {})
        location = displayed_location.get("location", "Unknown")

        prize_html = hackathon.get("prize_amount", "")
        submission_period_dates = hackathon.get("submission_period_dates", "Unknown")

        # Parse prize_amount to extract currency symbol and amount
        soup = BeautifulSoup(prize_html, 'html.parser')
        prize_text = soup.get_text(strip=True)  # E.g., "₹180,000" or "$20,000"

        if not prize_text:
            logger.debug(f"Hackathon '{title}' has no prize amount. Skipping.")
            continue

        # Extract currency symbol and numeric value
        # Assuming the first character is the currency symbol
        currency_symbol = prize_text[0]
        prize_amount_str = prize_text[1:].replace(',', '')  # Remove commas
        prize_amount = int(prize_amount_str) if prize_amount_str.isdigit() else 0

        # **Skip hackathons with excluded currencies**
        if currency_symbol not in symbol_to_currency:
            logger.debug(f"Skipping hackathon '{title}' due to excluded currency symbol: {currency_symbol}")
            continue

        # **Skip hackathons with zero prize amount**
        if prize_amount == 0:
            logger.debug(f"Skipping hackathon '{title}' because prize amount is zero.")
            continue

        # Determine the currency code
        currency_code = symbol_to_currency.get(currency_symbol, None)
        if not currency_code:
            logger.debug(f"Currency symbol '{currency_symbol}' not mapped to any currency code.")
            continue

        # Location check:
        loc_lower = location.lower()
        if "online" in loc_lower:
            logger.debug(f"Hackathon '{title}' is online.")
        else:
            # Confirm geocoding => BC, Canada
            if not is_in_british_columbia_google(location, GOOGLE_API_MAPS_KEY):
                logger.debug(f"Hackathon '{title}' is not in British Columbia. Skipping.")
                continue  # Skip if not in BC

        # If it passes the filters, construct the dictionary
        hackathon_dict = {
            "name": title,
            "url": url,
            "location": location,
            "prize": f"{currency_code}{prize_amount}",
            "date": submission_period_dates
        }

        # **Save to the hackathon cache**
        hackathon_cache[url] = hackathon_dict

        # **Append to filtered_hackathons**
        filtered_hackathons.append(hackathon_dict)
        logger.debug(f"Hackathon '{title}' added to filtered list with prize {hackathon_dict['prize']}.")

    # **Persist the updated cache**
    cache_data["hackathons"] = hackathon_cache
    save_cache(cache_data)
    logger.info(f"Total new filtered hackathons: {len(filtered_hackathons)}")

    return filtered_hackathons