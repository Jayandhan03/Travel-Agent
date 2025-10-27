import requests
import json


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
    
result = fetch_visa_info("IN", "ID")
print(result)