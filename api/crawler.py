import asyncio
import logging
import os
from typing import List, Dict

import aiohttp
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

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

SYMBOL_TO_CURRENCY = {
    '$': 'USD',
    'CAD': 'CAD',
}

async def fetch_hackathon_detail(session: aiohttp.ClientSession, url: str) -> str:
    """
    Asynchronously fetches the HTML content of a hackathon's detail page.
    """
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            html_content = await response.text()
            logger.debug(f"Fetched detail page for URL: {url}")
            return html_content
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching detail page for {url}: {e}", exc_info=True)
        return ""

def parse_hackathon_details(html_content: str) -> Dict:
    """
    Parses the hackathon detail page to extract additional information
    such as "US only" restriction.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    details = {}

    eligibility_items_text = [
        item.get_text(strip=True).lower()
        for item in soup.select('#eligibility-list li')
    ]
    details["eligibility_items"] = eligibility_items_text

    # Then to check "us only":
    details["us_only"] = any("us only" in entry for entry in eligibility_items_text)

    return details

async def fetch_all_hackathon_details(hackathons: List[Dict]) -> Dict[str, Dict]:
    """
    Asynchronously fetches and parses detailed information for all hackathons.
    Returns a mapping from hackathon URL to its detailed info.
    """
    detailed_info = {}
    async with aiohttp.ClientSession() as session:
        tasks = []
        for hackathon in hackathons:
            url = hackathon['url']
            tasks.append(fetch_hackathon_detail(session, url))

        html_contents = await asyncio.gather(*tasks)

        for hackathon, html in zip(hackathons, html_contents):
            if html:
                details = parse_hackathon_details(html)
                detailed_info[hackathon['url']] = details
            else:
                detailed_info[hackathon['url']] = {}

    return detailed_info

def is_target_audience(eligibility: str) -> bool:
    """
    Determines if the hackathon is suitable for the target audience based on eligibility criteria.
    Returns True if suitable, False otherwise.
    """
    # Define keywords that indicate non-target audiences
    excluded_keywords = ['Ages 13 to 18 only']

    for keyword in excluded_keywords:
        if keyword in eligibility:
            logger.debug(f"Eligibility contains excluded keyword: '{keyword}'")
            return False
    return True

def fetch_hackathon_data(api_url: str) -> List[Dict]:
    """
    Fetches hackathon data from Devpost's API endpoint, returning only hackathons
    that match certain filters:
      - Upcoming + recently added
      - Located in Vancouver/BC/Online
      - Awarding USD or CAD only (exclude hackathons with INR/₹, GBP/£, etc.)
      - Prize amount greater than zero
      - Suitable for target audience (e.g., not exclusively for high schoolers)
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
        if currency_symbol not in SYMBOL_TO_CURRENCY:
            logger.debug(f"Skipping hackathon '{title}' due to excluded currency symbol: {currency_symbol}")
            continue

        # **Skip hackathons with zero prize amount**
        if prize_amount == 0:
            logger.debug(f"Skipping hackathon '{title}' because prize amount is zero.")
            continue

        # Determine the currency code
        currency_code = SYMBOL_TO_CURRENCY.get(currency_symbol, None)
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

        # If it passes the initial filters, prepare to check detailed eligibility
        hackathon_dict = {
            "name": title,
            "url": url,
            "location": location,
            "prize": f"{currency_code}{prize_amount}",
            "date": submission_period_dates
        }

        # Append to the list for detailed checks
        filtered_hackathons.append(hackathon_dict)
        logger.debug(f"Hackathon '{title}' passed initial filters.")

    # === Fetch and parse detailed information asynchronously ===
    if filtered_hackathons:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        detailed_info = loop.run_until_complete(fetch_all_hackathon_details(filtered_hackathons))
        loop.close()

        # **Filter based on detailed eligibility**
        final_filtered_hackathons = []
        for hackathon in filtered_hackathons:
            url = hackathon['url']
            details = detailed_info.get(url, {})

            # 1) Skip if "US only" is detected
            if details.get("us_only", False):
                logger.debug(f"Hackathon '{hackathon['name']}' is US-only. Excluding.")
                continue

            # 2) If you also want to skip if it’s only for high/middle schoolers,
            eligibility = details.get('eligibility', "")
            if not is_target_audience(eligibility):
                logger.debug(f"Hackathon '{hackathon['name']}' excluded based on eligibility (e.g. high school).")
                continue

            # If everything is fine, add to final list:
            hackathon_cache[url] = hackathon
            final_filtered_hackathons.append(hackathon)
            logger.debug(f"Hackathon '{hackathon['name']}' added to final filtered list.")

        # **Persist the updated cache**
        cache_data["hackathons"] = hackathon_cache
        save_cache(cache_data)
        logger.info(f"Total new filtered hackathons: {len(final_filtered_hackathons)}")
        return final_filtered_hackathons

    else:
        logger.info("No new hackathons passed the initial filters.")
        return []

