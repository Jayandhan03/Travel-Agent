import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_flight_offers(
    departure_city: str,
    arrival_city: str,
    travel_date: str,
    travel_class: str = None,
    max_price: int = None,
    currency: str = "INR"
) -> dict:
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
            "max": 5,
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


# Example usage
if __name__ == "__main__":
    flights = get_flight_offers("DEL", "BOM", "2025-10-27", travel_class="BUSINESS")
    from pprint import pprint
    if "offers_extracted" in flights:
        pprint(flights["offers_extracted"])
    else:
        print(f"Error: {flights.get('error', 'Unknown error')}")



# Amadeus accepts IATA-standard cabin class codes for the travelClass parameter.

# Here are the allowed values:

# "ECONOMY"

# "PREMIUM_ECONOMY"

# "BUSINESS"

# "FIRST"

# ⚡ Notes:

# If you don’t set travelClass, Amadeus will return all available cabins.

# Some airlines don’t support all 4 cabins on every route (e.g., no PREMIUM_ECONOMY on domestic flights).

# You can’t pass multiple at once (e.g., "ECONOMY,BUSINESS" won’t work) — it’s one per query.