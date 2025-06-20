from typing import Optional, Dict
import httpx
import pandas as pd
import asyncio
from datetime import datetime

# API endpoints
API_URL = "http://api.sensors.africa/v2/data/"
LOCATIONS_URL = "http://api.sensors.africa/v2/locations/"
SENSOR_TYPES_URL = "http://api.sensors.africa/v2/sensor-types/"
SENSORS_URL = "http://api.sensors.africa/v2/sensors/"

COOKIES = {
    "csrftoken": "SokQeIlq97mpRNlU65M6L3o",
    "sessionid": "hsoksd6rlabl80thzf3givz5rnkgpkrm"
}

async def fetch_paginated(url: str, params: Optional[Dict] = None, max_pages: int = 10) -> list:
    results = []
    next_url = url
    page_count = 0

    async with httpx.AsyncClient(timeout=60) as client:
        while next_url and page_count < max_pages:
            response = await client.get(next_url, params=params, cookies=COOKIES)
            if response.status_code != 200:
                print(f"Error fetching {next_url}: {response.status_code}")
                break
            data = response.json()
            if isinstance(data, list):
                results.extend(data)
                break
            if isinstance(data, dict) and "results" in data:
                results.extend(data["results"])
                next_url = data.get("next")
                page_count += 1
            else:
                break
    return results

async def fetch_metadata():
    sensor_types, locations, sensors = await asyncio.gather(
        fetch_paginated(SENSOR_TYPES_URL),
        fetch_paginated(LOCATIONS_URL),
        fetch_paginated(SENSORS_URL)
    )
    return (
        {st["id"]: st for st in sensor_types},
        {loc["id"]: loc for loc in locations},
        {s["id"]: s for s in sensors}
    )

def enrich_data(record, sensor_types, locations, sensors):
    sensor_id = record["sensor"]
    location_id = record["location"]["id"]

    sensor_info = sensors.get(sensor_id, {})
    sensor_type_id = sensor_info.get("sensor_type")
    sensor_type = sensor_types.get(sensor_type_id, {})
    loc = locations.get(location_id, {})

    ts = pd.to_datetime(record["timestamp"])
    enriched = {
        "id": record["id"],
        "timestamp": ts.isoformat(),
        "sensor": sensor_id,
        "sensor_public": sensor_info.get("public"),
        "sensor_type_name": sensor_type.get("name"),
        "sensor_manufacturer": sensor_type.get("manufacturer"),
        "software_version": record.get("software_version"),
        "location_id": location_id,
        "location_traffic": loc.get("traffic_in_area"),
        "location_industry": loc.get("industry_in_area"),
        "location_oven": loc.get("oven_in_area"),
        "latitude": loc.get("latitude"),
        "longitude": loc.get("longitude"),
        "altitude": loc.get("altitude"),
        "city": loc.get("city"),
        "country": loc.get("country"),
        "hour": ts.hour,
        "day_of_week": ts.dayofweek,
        "is_weekend": 1 if ts.dayofweek >= 5 else 0,
    }

    # Flatten sensor readings
    for item in record.get("sensordatavalues", []):
        try:
            enriched[item["value_type"]] = float(item["value"])
        except:
            enriched[item["value_type"]] = None

    return enriched

async def retrieve_air_quality_data(country: Optional[str] = "Kenya",
                                    location_id: Optional[int] = None,
                                    max_pages: int = 5):
    print("🔄 Fetching metadata...")
    sensor_types, locations, sensors = await fetch_metadata()

    print(f"🌍 Fetching air quality data for {country}...")
    params = {"country": country, "page_size": 100}
    raw_data = await fetch_paginated(API_URL, params=params, max_pages=max_pages)

    print("⚙️ Enriching records...")
    enriched = [enrich_data(r, sensor_types, locations, sensors) for r in raw_data]

    if country:
        enriched = [r for r in enriched if r.get("country", "").lower() == country.lower()]
    if location_id:
        enriched = [r for r in enriched if r.get("location_id") == location_id]

    if not enriched:
        raise ValueError("No records after filtering.")

    df = pd.DataFrame(enriched)

    # Arrange columns: group sensor info next to sensor ID
    col_order = [
        "id", "timestamp",
        "sensor", "sensor_public", "sensor_type_name", "sensor_manufacturer",
        "software_version",
        "location_id", "location_traffic", "location_industry", "location_oven",
        "latitude", "longitude", "altitude", "city", "country",
        "humidity", "temperature", "P2", "P1", "P0",
        "hour", "day_of_week", "is_weekend"
    ]
    # Add any missing columns that appeared dynamically
    col_order += [c for c in df.columns if c not in col_order]
    df = df[col_order]

    filename = f"air_quality_{country.lower()}_{location_id or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Saved {len(df)} rows to {filename}")
    return df

# 🔽 Run script directly
if __name__ == "__main__":
    # Adjust country, location_id, and max_pages as needed
    asyncio.run(retrieve_air_quality_data(country="Kenya", location_id=3967, max_pages=20))
