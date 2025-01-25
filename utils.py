import requests


def is_in_british_columbia_google(address: str, api_key: str) -> bool:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()

    # If no results, skip
    if not data.get("results"):
        return False

    # The first result
    result = data["results"][0]

    # parse address_components
    for component in result["address_components"]:
        # 'types' might be ["administrative_area_level_1", "political"] for a province
        if "administrative_area_level_1" in component["types"]:
            province = component["long_name"].lower()
            if province != "british columbia":
                return False
        if "country" in component["types"]:
            country = component["short_name"].lower()
            if country != "ca":
                return False

    return True