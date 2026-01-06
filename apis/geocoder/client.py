import requests


class Geocoder:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://us1.locationiq.com/v1/search"

    def geocode(self, query: str):
        params = {
            "key": self.api_key,
            "q": query,
            "format": "json",
            "limit": 1
        }

        response = requests.get(self.base_url, params=params)
        response.raise_for_status()

        data = response.json()

        if not data:
            raise ValueError(f"No results found for: {query}")

        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])

        return lat, lon
