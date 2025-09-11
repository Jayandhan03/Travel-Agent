import requests, os
from dotenv import load_dotenv

load_dotenv()

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


# Example usage
if __name__ == "__main__":
    hotels = get_hotels_tool("Mumbai", "2025-09-09", "2025-09-12", adults=2, hotel_class="5", min_price=3000, max_price=7000)
    from pprint import pprint
    pprint(hotels)
