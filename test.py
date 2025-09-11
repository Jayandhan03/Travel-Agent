import requests
import json,os
from dotenv import load_dotenv

load_dotenv()   

def get_activities_opentripmap(city: str, limit: int = 5):
    """
    Fetch top tourist attractions in a city using OpenTripMap API.
    """
    API_KEY = os.getenv("OPENTRIMAP_API_KEY")

    # Step 1: Get city coordinates
    geo_url = "https://api.opentripmap.com/0.1/en/places/geoname"
    geo_params = {"name": city, "apikey": API_KEY}
    geo_resp = requests.get(geo_url, params=geo_params)
    geo_resp.raise_for_status()
    geo_data = geo_resp.json()
    lat = geo_data.get("lat")
    lon = geo_data.get("lon")
    if not lat or not lon:
        return {"error": "City not found, cannot get coordinates"}

    # Step 2: Get attractions by radius
    radius_url = "https://api.opentripmap.com/0.1/en/places/radius"
    radius_params = {
        "radius": 5000,   # 5km radius
        "lon": lon,
        "lat": lat,
        "limit": limit,
        "apikey": API_KEY,
        "rate": 3,        
        "format": "json"
    }
    resp = requests.get(radius_url, params=radius_params)
    resp.raise_for_status()
    places = resp.json()

    activities = []
    for place in places:
        activities.append({
            "name": place.get("name"),
            "kinds": place.get("kinds"),
            "dist": place.get("dist")  # distance from city center
        })

    return activities
    
result = get_activities_opentripmap("Bali", "5")
print(result)