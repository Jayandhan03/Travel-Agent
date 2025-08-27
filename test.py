import os
import requests
from dotenv import load_dotenv
from langchain.tools import tool

# Load .env variables once
load_dotenv()

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

# --- Test the tool ---
if __name__ == "__main__":
    city = "London"
    check_in = "2025-08-29"
    check_out = "2025-08-31"
    adults = 2

    # Use invoke with a dict as required by LangChain
    result = get_hotels_tool.invoke({
        "city": city,
        "check_in": check_in,
        "check_out": check_out,
        "adults": adults
    })
    print(result)
