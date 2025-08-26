from langchain.tools import tool
from geopy.geocoders import Nominatim

@tool
def get_country_code(location_name: str) -> str:
    """
    LangChain tool: Convert a city/country name to its ISO country code (uppercase).
    """
    geolocator = Nominatim(user_agent="trip_planner")
    try:
        location = geolocator.geocode(location_name, language="en")
        if location and location.raw.get("address", {}).get("country_code"):
            return location.raw["address"]["country_code"].upper()
    except Exception:
        return "UNKNOWN"
    return "UNKNOWN"
