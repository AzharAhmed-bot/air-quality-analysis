import asyncio
import httpx
import json
from datetime import datetime

API_URL = "http://api.sensors.africa/v2/locations/"  
cookies = {
    "csrftoken": "guPCWQUdaqqIfuAcBuQ0QHFmC83cTMFxE28B4oLdhhAFOBOYv7OklJOI2B4bID5v",
    "sessionid": "iiv03hdqphfumar35hjeb2m5ydt5orng"
}

async def fetch_and_save_locations(country_name: str = "Kenya") -> str:
    """
    Fetch all sensor locations, filter by country, and save to JSON.
    :param country_name: Country name string to filter (default: 'Kenya')
    :return: path to saved JSON file
    """
    async with httpx.AsyncClient(timeout=60, cookies=cookies) as client:
        response = await client.get(API_URL)
        if response.status_code != 200:
            raise RuntimeError(f"❌ Error fetching {API_URL}: {response.status_code}")

        data = response.json()

    # API directly returns list of locations
    results = data if isinstance(data, list) else data.get("results", [])
    filtered = [loc for loc in results if loc.get("country") == country_name]

    # Save to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{country_name.lower()}_locations_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(filtered)} {country_name} locations to {filename}")
    return filename


# Example usage
if __name__ == "__main__":
    asyncio.run(fetch_and_save_locations("Kenya"))
