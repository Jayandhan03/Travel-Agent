import requests
import json

# Define the passport and destination countries using ISO 2 country codes
passport_country_code = "HK"  # Hong Kong
destination_country_code = "US"  # United Kingdom

# Construct the API URL
url = f"https://rough-sun-2523.fly.dev/visa/{passport_country_code}/{destination_country_code}"

try:
    # Make the GET request to the API
    response = requests.get(url, timeout=15)

    # Raise an exception for bad status codes (4xx or 5xx)
    response.raise_for_status()

    # Parse the JSON response
    data = response.json()

    # Pretty print the JSON data
    print(json.dumps(data, indent=4))

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
    # Try to print the error response from the API if available
    try:
        print(f"API Error Response: {response.json()}")
    except json.JSONDecodeError:
        print(f"Raw Error Response: {response.text}")
except requests.exceptions.RequestException as err:
    print(f"An error occurred: {err}")