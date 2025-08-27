from typing import  Literal
from langchain_core.tools import tool
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()


@tool("fetch_visa_info", return_direct=True)
def fetch_visa_info(passport_country_code: str, destination_country_code: str) -> str:
    """
    LangChain Tool:
    Given a passport country code (ISO Alpha-2) and destination country code,
    fetch the visa requirements info via external API.

    Example:
        Input: ("HK", "US")
        Output: JSON string containing visa information
    """
    url = f"https://rough-sun-2523.fly.dev/visa/{passport_country_code}/{destination_country_code}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        return json.dumps(data, indent=4)
    except requests.exceptions.HTTPError as http_err:
        try:
            return f"HTTP error: {http_err}\nAPI Response: {response.json()}"
        except Exception:
            return f"HTTP error: {http_err}\nRaw Response: {response.text}"
    except requests.exceptions.RequestException as err:
        return f"Request error: {err}"
    
@tool
def get_weather(place: str) -> dict:
    """
    Get the current weather forecast for a given place (city/town/village).
    Uses OpenStreetMap for geocoding and Open-Meteo for weather data.
    """
    # 1. Geocode the place -> lat/lon
    geo_url = "https://nominatim.openstreetmap.org/search"
    geo_params = {"q": place, "format": "json", "limit": 1}
    geo_resp = requests.get(geo_url, params=geo_params, headers={"User-Agent": "langchain-tool"})
    geo_resp.raise_for_status()
    geo_data = geo_resp.json()
    if not geo_data:
        return {"error": f"Could not find location: {place}"}
    
    lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]

    # 2. Fetch weather from Open-Meteo
    weather_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
    }
    weather_resp = requests.get(weather_url, params=params)
    weather_resp.raise_for_status()
    weather_data = weather_resp.json()

    return {
        "place": place,
        "latitude": lat,
        "longitude": lon,
        "current_weather": weather_data.get("current_weather", {}),
    }


@tool
def get_flight_offers(departure_city: str, arrival_city: str, travel_date: str) -> dict:
    """
    Fetch available flight offers from Amadeus API for a given route and date.

    Args:
        departure_city (str): IATA code of the departure city (e.g., "DEL").
        arrival_city (str): IATA code of the arrival city (e.g., "BOM").
        travel_date (str): Date of travel in YYYY-MM-DD format.

    Returns:
        dict: A dictionary with flight offers or an error message.
    """
    try:
        # 1. Get API credentials
        api_key = os.getenv("AMADEUS_API_KEY")
        api_secret = os.getenv("AMADEUS_API_SECRET")

        if not api_key or not api_secret:
            return {"error": "Missing API credentials in .env file"}

        # 2. Fetch access token
        token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": api_secret,
        }
        token_resp = requests.post(token_url, data=payload)
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")

        if not access_token:
            return {"error": "Failed to retrieve access token"}

        # 3. Fetch flight offers
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        params = {
            "originLocationCode": departure_city,
            "destinationLocationCode": arrival_city,
            "departureDate": travel_date,
            "adults": 1,
            "max": 5,
        }
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()

        return {
            "departure_city": departure_city,
            "arrival_city": arrival_city,
            "travel_date": travel_date,
            "offers": resp.json().get("data", []),
        }

    except requests.HTTPError as e:
        return {"error": f"HTTP Error: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}
    

@tool
def get_hotels_tool(city: str, check_in: str, check_out: str, adults: int = 2):
    """
    LangChain tool to fetch hotel data using SerpApi Google Hotels API.
    Reads the API key from the environment inside the function.
    Args:
        city (str): City name
        check_in (str): Check-in date YYYY-MM-DD
        check_out (str): Check-out date YYYY-MM-DD
        adults (int): Number of adults
    Returns:
        str: Formatted top hotel results
    """
    # Get the API key inside the function
    SERP_API_KEY = os.getenv("SERP_API_KEY")
    if not SERP_API_KEY:
        return "Error: SERP_API_KEY not found in environment variables."

    url = f"https://serpapi.com/search?engine=google_hotels&q={city}&check_in_date={check_in}&check_out_date={check_out}&adults={adults}&api_key={SERP_API_KEY}"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return f"Error: Received status {response.status_code} - {response.text}"

        data = response.json()
        if "properties" not in data:
            return "No hotel properties found in the response."

        results = []
        for i, hotel in enumerate(data['properties'][:10]):  # top 10 hotels
            name = hotel.get('name', 'N/A')
            rating = hotel.get('overall_rating', 'N/A')
            reviews = hotel.get('reviews', 0)
            price = hotel.get('rate_per_night', {}).get('lowest', 'N/A')
            results.append(f"{i+1}. {name} - Rating: {rating} ({reviews} reviews) - Price per night: {price}")
        
        return "\n".join(results)
    except Exception as e:
        return f"Exception occurred: {e}"

@tool
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
        "rate": 3,        # optional: filter by popularity
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

