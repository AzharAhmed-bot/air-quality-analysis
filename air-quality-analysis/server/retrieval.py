from typing import Optional, Dict
import httpx
import pandas as pd
import asyncio
from datetime import datetime

# =====================================================
# GLOBAL SET TO TRACK UNIQUE LOCATIONS
# =====================================================
locations_installed = set()

# ------------------- API URLs -------------------
API_URL = "http://api.sensors.africa/v2/data/"
NOW_URL = "http://api.sensors.africa/v2/now/"
LOCATIONS_URL = "http://api.sensors.africa/v2/locations/"
SENSOR_TYPES_URL = "http://api.sensors.africa/v2/sensor-types/"
SENSORS_URL = "http://api.sensors.africa/v2/sensors/"

# ------------------- Auth Cookies -------------------
COOKIES = {
    "csrftoken": "guPCWQUdaqqIfuAcBuQ0QHFmC83cTMFxE28B4oLdhhAFOBOYv7OklJOI2B4bID5v",
    "sessionid": "iiv03hdqphfumar35hjeb2m5ydt5orng"
}

# =====================================================
# PAGINATION FETCHER
# =====================================================
async def fetch_paginated(url: str, params: Optional[Dict] = None, max_pages: int = 10) -> list:
    results = []
    next_url = url
    page_count = 0

    async with httpx.AsyncClient(timeout=60) as client:
        while next_url and page_count < max_pages:
            print(f"📥 Fetching page {page_count+1} ...")
            response = await client.get(next_url, params=params if page_count == 0 else None, cookies=COOKIES)
            if response.status_code != 200:
                print(f"❌ Error fetching {next_url}: {response.status_code}")
                break

            data = response.json()
            if isinstance(data, dict) and "results" in data:
                results.extend(data["results"])
                next_url = data.get("next")
            elif isinstance(data, list):
                results.extend(data)
                break
            else:
                break

            page_count += 1

    print(f"✅ Done. Collected {len(results)} records over {page_count} pages.")
    return results

# =====================================================
# METADATA FETCH
# =====================================================
async def fetch_metadata():
    sensor_types, locations, sensors = await asyncio.gather(
        fetch_paginated(SENSOR_TYPES_URL, max_pages=5),
        fetch_paginated(LOCATIONS_URL, max_pages=5),
        fetch_paginated(SENSORS_URL, max_pages=5)
    )
    return (
        {st["id"]: st for st in sensor_types},
        {loc["id"]: loc for loc in locations},
        {s["id"]: s for s in sensors}
    )

# =====================================================
# ENRICH DATA (/data)
# =====================================================
def enrich_data(record, sensor_types, locations, sensors):
    sensor_id = record["sensor"]
    location_id = record["location"]["id"]

    # 🔹 Add location to global set
    locations_installed.add(location_id)

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

    for item in record.get("sensordatavalues", []):
        try:
            enriched[item["value_type"]] = float(item["value"])
        except:
            enriched[item["value_type"]] = None

    return enriched


async def retrieve_air_quality_data(country: Optional[str] = "Kenya",
                                    location_id: Optional[int] = None,
                                    max_pages: int = 20000):
    print("🔄 Fetching metadata...")
    sensor_types, locations, sensors = await fetch_metadata()

    # ---------------- Time bounds (last 24 hours) ----------------
    now = datetime.utcnow()
    yesterday = now - pd.Timedelta(days=1)

    params = {
        "location__country": country,             
        "timestamp__gte": yesterday.isoformat(), 
        "timestamp__lte": now.isoformat()
    }

    print(f"🌍 Fetching air quality data for {country} (last 24h, up to {max_pages} pages)...")
    raw_data = await fetch_paginated(API_URL, params=params, max_pages=max_pages)

    print("⚙️ Enriching records...")
    enriched = [enrich_data(r, sensor_types, locations, sensors) for r in raw_data]

    if location_id:
        enriched = [r for r in enriched if r.get("location_id") == location_id]

    if not enriched:
        raise ValueError("No records after filtering.")

    df = pd.DataFrame(enriched)

    # Ensure critical columns exist
    for col in ["humidity", "temperature", "P2", "P1", "P0"]:
        if col not in df.columns:
            df[col] = None
    
    df = df.sort_values(by=["location_id", "timestamp"]).reset_index(drop=True)

    filename = f"air_quality_{country.lower()}_{location_id or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Saved {len(df)} rows to {filename}")

    # 🔹 Print unique location count
    print(f"📌 Found {len(locations_installed)} unique locations in dataset.")

    return df

# =====================================================
# ENRICH DATA (/now)
# =====================================================
def enrich_now_record(record):
    ts = pd.to_datetime(record["timestamp"])
    sensor = record.get("sensor", {})
    sensor_type = sensor.get("sensor_type", {})
    loc = record.get("location", {})

    enriched = {
        "id": record["id"],
        "timestamp": ts.isoformat(),
        "sensor": sensor.get("id"),
        "sensor_pin": sensor.get("pin"),
        "sensor_type_name": sensor_type.get("name"),
        "sensor_manufacturer": sensor_type.get("manufacturer"),
        "software_version": record.get("software_version"),
        "location_id": loc.get("id"),
        "latitude": loc.get("latitude"),
        "longitude": loc.get("longitude"),
        "altitude": loc.get("altitude"),
        "city": loc.get("city"),
        "country": loc.get("country"),
        "hour": ts.hour,
        "day_of_week": ts.dayofweek,
        "is_weekend": 1 if ts.dayofweek >= 5 else 0,
    }

    for item in record.get("sensordatavalues", []):
        try:
            enriched[item["value_type"]] = float(item["value"])
        except:
            enriched[item["value_type"]] = None

    return enriched


async def retrieve_air_quality_now():
    print("🌍 Fetching latest snapshot (/now)...")

    async with httpx.AsyncClient(timeout=60, cookies=COOKIES) as client:
        response = await client.get(NOW_URL)
        if response.status_code != 200:
            raise ValueError(f"Error fetching /now: {response.status_code}")
        raw_data = response.json()

    print("⚙️ Enriching records...")
    enriched = [enrich_now_record(r) for r in raw_data]

    if not enriched:
        raise ValueError("No records retrieved from /now.")

    df = pd.DataFrame(enriched)

    # Ensure critical columns exist
    for col in ["humidity", "temperature", "P2", "P1", "P0"]:
        if col not in df.columns:
            df[col] = None

    filename = f"air_quality_now_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Saved {len(df)} rows to {filename}")
    return df

# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    mode = "data"   

    if mode == "data":
        asyncio.run(retrieve_air_quality_data(country='Kenya', max_pages=20000))
    elif mode == "now":
        asyncio.run(retrieve_air_quality_now())
