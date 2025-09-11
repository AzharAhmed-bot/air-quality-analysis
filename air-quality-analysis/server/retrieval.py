from typing import Optional, Dict
import httpx
import pandas as pd
import asyncio
from datetime import datetime
import numpy as np

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

# =====================================================
# DATA QUALITY ANALYSIS
# =====================================================
def analyze_data_quality(df):
    """Analyze missing values and data quality"""
    print("\n📊 DATA QUALITY ANALYSIS")
    print("=" * 50)
    
    # Missing values summary
    missing_summary = df.isnull().sum()
    missing_percent = (missing_summary / len(df)) * 100
    
    quality_df = pd.DataFrame({
        'Missing_Count': missing_summary,
        'Missing_Percent': missing_percent
    }).sort_values('Missing_Percent', ascending=False)
    
    print(quality_df[quality_df['Missing_Count'] > 0])
    
    # Location coverage
    locations_with_dht = df[df['sensor_type_name'].str.contains('DHT', case=False, na=False)]['location_id'].nunique()
    locations_with_pms = df[df['sensor_type_name'].str.contains('PMS', case=False, na=False)]['location_id'].nunique()
    total_locations = df['location_id'].nunique()
    
    print(f"\n📍 LOCATION COVERAGE:")
    print(f"Total locations: {total_locations}")
    print(f"Locations with DHT sensors: {locations_with_dht}")
    print(f"Locations with PMS sensors: {locations_with_pms}")
    
    return quality_df

# =====================================================
# ENHANCED SENSOR MERGING WITH MISSING VALUE HANDLING
# =====================================================
def merge_sensors(df, time_window="15min", fill_strategy="interpolate"):
    """
    Enhanced sensor merging with multiple strategies for handling missing values
    
    Parameters:
    - time_window: tolerance for timestamp matching
    - fill_strategy: 'interpolate', 'forward_fill', 'backward_fill', 'drop', or 'keep_all'
    """
    print(f"\n🔗 MERGING SENSORS (time_window={time_window}, fill_strategy={fill_strategy})")
    
    # Analyze data quality before merging
    analyze_data_quality(df)
    
    # Split DHT vs PMS
    dht = df[df["sensor_type_name"].str.contains("DHT", case=False, na=False)].copy()
    pms = df[df["sensor_type_name"].str.contains("PMS", case=False, na=False)].copy()

    print(f"DHT records: {len(dht)}, PMS records: {len(pms)}")

    # Robust timestamp parsing
    dht["timestamp"] = pd.to_datetime(dht["timestamp"], utc=True, format="mixed")
    pms["timestamp"] = pd.to_datetime(pms["timestamp"], utc=True, format="mixed")

    # Sort
    dht = dht.sort_values(["location_id", "timestamp"])
    pms = pms.sort_values(["location_id", "timestamp"])

    # Create sensor metadata lookup tables for each location
    dht_metadata = dht.groupby('location_id').agg({
        'sensor_type_name': 'first',
        'sensor_manufacturer': 'first',
        'sensor': 'first'
    }).rename(columns={
        'sensor_type_name': 'dht_sensor_type',
        'sensor_manufacturer': 'dht_manufacturer',
        'sensor': 'dht_sensor_id'
    })

    pms_metadata = pms.groupby('location_id').agg({
        'sensor_type_name': 'first',
        'sensor_manufacturer': 'first', 
        'sensor': 'first'
    }).rename(columns={
        'sensor_type_name': 'pms_sensor_type',
        'sensor_manufacturer': 'pms_manufacturer',
        'sensor': 'pms_sensor_id'
    })

    # Select columns for merge
    dht_cols = ["timestamp", "location_id", "humidity", "temperature", 
                "sensor_type_name", "sensor_manufacturer", "sensor"]
    
    # Only include columns that exist
    dht_cols = [col for col in dht_cols if col in dht.columns]
    
    dht_useful = dht[dht_cols].rename(columns={
        "sensor_type_name": "dht_sensor_type",
        "sensor_manufacturer": "dht_manufacturer", 
        "sensor": "dht_sensor_id"
    })

    pms_cols = ["timestamp", "location_id", "P2", "P1", "P0",
                "latitude", "longitude", "altitude", "city", "country",
                "sensor_type_name", "sensor_manufacturer", "sensor"]
    
    # Only include columns that exist
    pms_cols = [col for col in pms_cols if col in pms.columns]
    
    pms_useful = pms[pms_cols].rename(columns={
        "sensor_type_name": "pms_sensor_type",
        "sensor_manufacturer": "pms_manufacturer",
        "sensor": "pms_sensor_id"
    })

    if fill_strategy == "keep_all":
        # Use outer merge to keep all records
        merged = pd.merge(
            pms_useful, dht_useful,
            on=["location_id"], 
            how="outer",
            suffixes=("_pms", "_dht")
        )
    else:
        # Merge on nearest timestamp within tolerance
        merged = pd.merge_asof(
            pms_useful.sort_values("timestamp"),
            dht_useful.sort_values("timestamp"),
            on="timestamp",
            by="location_id",
            direction="nearest",
            tolerance=pd.Timedelta(time_window)
        )

    print(f"Records after merge: {len(merged)}")

    # Handle missing values based on strategy
    if fill_strategy == "interpolate":
        # First, interpolate numeric values within each location
        numeric_cols = merged.select_dtypes(include=[np.number]).columns
        merged_filled = merged.groupby('location_id')[numeric_cols].transform(
            lambda x: x.interpolate(method='linear', limit_direction='both')
        )
        merged[numeric_cols] = merged_filled
        
        # Then fill missing categorical sensor metadata using location-based lookup
        print("🔧 Filling missing sensor metadata...")
        
        # Fill missing DHT metadata
        dht_meta_cols = ['dht_sensor_type', 'dht_manufacturer', 'dht_sensor_id']
        for col in dht_meta_cols:
            if col in merged.columns:
                # Fill with location-specific sensor metadata
                merged[col] = merged[col].fillna(
                    merged['location_id'].map(dht_metadata[col.replace('dht_', '')] if col.replace('dht_', '') in dht_metadata.columns else {})
                )
        
        # Fill missing PMS metadata
        pms_meta_cols = ['pms_sensor_type', 'pms_manufacturer', 'pms_sensor_id']  
        for col in pms_meta_cols:
            if col in merged.columns:
                # Fill with location-specific sensor metadata
                merged[col] = merged[col].fillna(
                    merged['location_id'].map(pms_metadata[col.replace('pms_', '')] if col.replace('pms_', '') in pms_metadata.columns else {})
                )
        
        # For any remaining missing categorical values, use forward/backward fill within location
        categorical_cols = merged.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            merged[col] = merged.groupby('location_id')[col].transform(
                lambda x: x.fillna(method='ffill').fillna(method='bfill')
            )
        
    elif fill_strategy == "forward_fill":
        merged = merged.groupby('location_id').fillna(method='ffill')
        
    elif fill_strategy == "backward_fill":
        merged = merged.groupby('location_id').fillna(method='bfill')
        
    elif fill_strategy == "drop":
        # Drop rows with any missing values in key columns
        key_cols = ['humidity', 'temperature', 'P2', 'P1']
        key_cols = [col for col in key_cols if col in merged.columns]
        merged = merged.dropna(subset=key_cols)

    # Final sort and reset index - ensure we have required columns first
    sort_columns = []
    if 'location_id' in merged.columns:
        sort_columns.append('location_id')
    if 'timestamp' in merged.columns:
        sort_columns.append('timestamp')
    
    if sort_columns:
        merged = merged.sort_values(by=sort_columns).reset_index(drop=True)
    else:
        merged = merged.reset_index(drop=True)
        print("⚠️ Warning: Could not sort by location_id/timestamp - columns not found")
    
    # Print final data quality
    print(f"\n✅ FINAL MERGED DATA QUALITY:")
    missing_after = merged.isnull().sum()
    print(missing_after[missing_after > 0])
    
    return merged

# =====================================================
# RETRIEVE AIR QUALITY DATA WITH ENHANCED PROCESSING
# =====================================================
async def retrieve_air_quality_data(country: Optional[str] = "Kenya",
                                    location_id: Optional[int] = None,
                                    max_pages: int = 20000,
                                    merge_strategy: str = "interpolate",
                                    time_window: str = "15min"):
    print("🔄 Fetching metadata...")
    sensor_types, locations, sensors = await fetch_metadata()

    # Time bounds (last 24 hours)
    now = datetime.utcnow()
    two_days_ago = now - pd.Timedelta(days=2)

    params = {
        "location__country": country,
        "timestamp__gte": two_days_ago.isoformat(),
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
    for col in ["humidity", "temperature", "P2", "P1", "P0","altitude"]:
        if col not in df.columns:
            df[col] = None

    df = df.sort_values(by=["location_id", "timestamp"]).reset_index(drop=True)

    # Save raw data
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    # raw_filename = f"air_quality_raw_{country.lower()}_{location_id or 'all'}_{timestamp_str}.csv"
    # df.to_csv(raw_filename, index=False)
    # print(f"✅ Saved raw dataset with {len(df)} rows to {raw_filename}")

    # Enhanced merge with missing value handling
    df_merged = merge_sensors(df, time_window=time_window, fill_strategy=merge_strategy)
    
    merged_filename = f"air_quality_merged_{country.lower()}_{location_id or 'all'}_{merge_strategy}_{timestamp_str}.csv"
    df_merged.to_csv(merged_filename, index=False)
    print(f"✅ Saved merged dataset with {len(df_merged)} rows to {merged_filename}")

    print(f"📌 Found {len(locations_installed)} unique locations in dataset.")

    return df, df_merged

# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":

    
    asyncio.run(retrieve_air_quality_data(
        country='Kenya', 
        max_pages=20000,
        merge_strategy="drop", 
        time_window="30min"            
    ))