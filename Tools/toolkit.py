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
    

@tool("get_weather_forecast", return_direct=True)
def get_weather(place: str, start_date: str, end_date: str) -> dict:
    """
    Get the weather forecast for a given place between start_date and end_date.
    Dates must be within the next ~16 days (Open-Meteo limit).

    Args:
        place: City/town/village name
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Dict with location details and forecast (daily max/min temp, precipitation, wind).
    """
    # 1. Geocode place
    geo_url = "https://nominatim.openstreetmap.org/search"
    geo_params = {"q": place, "format": "json", "limit": 1}
    geo_resp = requests.get(geo_url, params=geo_params, headers={"User-Agent": "trip-weather-tool"})
    geo_resp.raise_for_status()
    geo_data = geo_resp.json()
    if not geo_data:
        return {"error": f"Could not find location: {place}"}
    
    lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]

    # 2. Fetch forecast
    weather_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max","temperature_2m_min","precipitation_sum","windspeed_10m_max"],
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date
    }
    weather_resp = requests.get(weather_url, params=params)
    weather_resp.raise_for_status()
    weather_data = weather_resp.json()

    return {
        "place": place,
        "latitude": lat,
        "longitude": lon,
        "forecast": weather_data.get("daily", {}),
    }


@tool
def get_flight_offers(departure_city: str,arrival_city: str,travel_date: str,travel_class: str = None,max_price: int = None,currency: str = "INR") -> dict:
    """
    Fetch available flight offers from Amadeus API for a given route and date.
    Returns both raw JSON and extracted structured details.
    """

    try:
        # 1. API credentials
        api_key = os.getenv("AMADEUS_API_KEY")
        api_secret = os.getenv("AMADEUS_API_SECRET")
        if not api_key or not api_secret:
            return {"error": "Missing API credentials in .env file"}

        # 2. Access token
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

        # 3. Fetch offers
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "originLocationCode": departure_city,
            "destinationLocationCode": arrival_city,
            "departureDate": travel_date,
            "adults": 1,
            "currencyCode": currency,
            "max": 1,
        }
        if travel_class:
            params["travelClass"] = travel_class
        if max_price:
            params["maxPrice"] = max_price

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        offers = resp.json().get("data", [])

        # fallback if strict filter yields nothing
        if not offers:
            params.pop("maxPrice", None)
            resp = requests.get(url, headers=headers, params=params)
            resp.raise_for_status()
            offers = resp.json().get("data", [])

        if not offers:
            return {"error": "No flights found for given criteria."}

        # 4. Extract structured details
        extracted = []
        for offer in offers:
            price = offer.get("price", {}).get("total", "N/A")
            itineraries = offer.get("itineraries", [])
            segments = itineraries[0].get("segments", []) if itineraries else []

            flight_segments = []
            for seg in segments:
                flight_segments.append({
                    "carrier": seg.get("carrierCode"),
                    "flight_number": seg.get("number"),
                    "departure_airport": seg["departure"].get("iataCode"),
                    "departure_time": seg["departure"].get("at"),
                    "arrival_airport": seg["arrival"].get("iataCode"),
                    "arrival_time": seg["arrival"].get("at"),
                    "duration": seg.get("duration")
                })

            extracted.append({
                "price": f"{price} {currency}",
                "segments": flight_segments
            })

        # 5. Return both raw + extracted
        return {
            "departure_city": departure_city,
            "arrival_city": arrival_city,
            "travel_date": travel_date,
            "offers_raw": offers,       # full API response data
            "offers_extracted": extracted  # clean structured summary
        }

    except requests.HTTPError as e:
        return {"error": f"HTTP Error: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}


@tool
def get_hotels_tool(city: str, check_in: str, check_out: str, adults: int = 2,
                    hotel_class: str = None, min_price: int = None, max_price: int = None):
    """
    Fetch hotel properties from SerpAPI Google Hotels.
    Returns a concise list of top hotels with only available information.
    """

    SERP_API_KEY = os.getenv("SERP_API_KEY")
    if not SERP_API_KEY:
        return {"error": "SERP_API_KEY not found in environment variables."}

    base_url = "https://serpapi.com/search"

    def fetch(params):
        try:
            response = requests.get(base_url, params=params)
            if response.status_code != 200:
                return {"error": f"Received status {response.status_code} - {response.text}"}, None

            data = response.json()
            properties = data.get("properties", [])
            if not properties:
                return None, data

            results = []
            for hotel in properties[:10]:  # Top 10 hotels
                hotel_data = {}
                if hotel.get("name"):
                    hotel_data["name"] = hotel["name"]
                if hotel.get("star_rating"):
                    hotel_data["star_rating"] = hotel["star_rating"]
                if hotel.get("overall_rating"):
                    hotel_data["overall_rating"] = hotel["overall_rating"]
                if hotel.get("rate_per_night", {}).get("lowest"):
                    hotel_data["price_per_night"] = hotel["rate_per_night"]["lowest"]
                if hotel.get("address"):
                    hotel_data["address"] = hotel["address"]
                if hotel.get("booking_url"):
                    hotel_data["booking_url"] = hotel["booking_url"]

                if hotel_data:  # Only add hotels with at least one field
                    results.append(hotel_data)

            return results, data
        except Exception as e:
            return {"error": f"Exception occurred: {e}"}, None

    # Base parameters
    params = {
        "engine": "google_hotels",
        "q": city,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": adults,
        "api_key": SERP_API_KEY,
    }
    if hotel_class:
        params["hotel_class"] = hotel_class
    if min_price:
        params["min_price"] = min_price
    if max_price:
        params["max_price"] = max_price

    # First attempt with all filters
    result, _ = fetch(params)
    if result:
        return result

    # Fallback: drop price filters
    if min_price or max_price:
        params.pop("min_price", None)
        params.pop("max_price", None)
        result, _ = fetch(params)
        if result:
            return {"warning": f"No matches in given price range, showing available {hotel_class}-star hotels", "hotels": result}

    # Fallback: drop hotel class
    params.pop("hotel_class", None)
    result, _ = fetch(params)
    if result:
        return {"warning": f"No matches for {hotel_class}-star hotels, showing all available hotels", "hotels": result}

    return {"error": "No hotel properties found even after fallback."}


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

