"""
Data Pipeline for NYC Taxi Data Explorer
-----------------------------------------
Loads, cleans, and enriches raw TLC trip records.
Output is saved to processed/cleaned_trips.csv and used by load_data_to_sql.py.

Steps:
    1. load_data        — read raw CSV and zone lookup
    2. clean_trips      — remove nulls, duplicates, and out-of-range rows
    3. engineer_features — add duration, speed, fare-per-mile columns
    4. integrate_lookup  — join zone names and boroughs onto trips
    5. save_output       — write cleaned_trips.csv to processed/
"""

import pandas as pd
import os

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
DATA_DIR       = os.path.join(BASE_DIR, "..", "data")
PROCESSED_DIR  = os.path.join(BASE_DIR, "processed")
LOG_DIR        = os.path.join(BASE_DIR, "logs")

PARQUET_PATH     = os.path.join(DATA_DIR, "yellow_tripdata_2019-01.parquet")
CSV_PATH         = os.path.join(DATA_DIR, "yellow_tripdata_2019-01.csv")
ZONE_LOOKUP_PATH = os.path.join(DATA_DIR, "taxi_zone_lookup.csv")

REQUIRED_COLUMNS = {"tpep_pickup_datetime", "tpep_dropoff_datetime",
                    "PULocationID", "DOLocationID", "fare_amount", "trip_distance"}

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


# ── STEP 1: Load ───────────────────────────────────────────────────────────────

def load_data():
    print("Loading datasets...")

    trips = None

    # Try parquet first (smaller, faster), fall back to CSV
    if os.path.exists(PARQUET_PATH):
        print("  Reading parquet file...")
        trips = pd.read_parquet(PARQUET_PATH)
        trips = trips.head(600_000)
    elif os.path.exists(CSV_PATH):
        print("  Reading CSV file...")
        trips = pd.read_csv(CSV_PATH, nrows=600_000)
    else:
        print("\n  ERROR: No trip data file found.")
        print("  Download one of:")
        print(f"    Parquet: curl -o data/yellow_tripdata_2019-01.parquet \\")
        print(f"      https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2019-01.parquet")
        print(f"    CSV:     curl -o data/yellow_tripdata_2019-01.csv \\")
        print(f"      https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2019-01.csv")
        return None, None

    # Validate the file actually contains trip data
    missing = REQUIRED_COLUMNS - set(trips.columns)
    if missing:
        print(f"\n  ERROR: Trip file is missing columns: {missing}")
        print("  The file may be corrupted or was downloaded incorrectly.")
        print("  Re-download using the curl command in the README.")
        return None, None

    zone_lookup = pd.read_csv(ZONE_LOOKUP_PATH)

    print(f"  Loaded {len(trips):,} trip rows and {len(zone_lookup):,} zone records.")
    return trips, zone_lookup


# ── STEP 2: Clean ─────────────────────────────────────────────────────────────

def clean_trips(trips):
    print("Cleaning trip data...")
    original = len(trips)

    # Parse datetimes
    trips["tpep_pickup_datetime"]  = pd.to_datetime(trips["tpep_pickup_datetime"],  errors="coerce")
    trips["tpep_dropoff_datetime"] = pd.to_datetime(trips["tpep_dropoff_datetime"], errors="coerce")
    trips = trips.dropna(subset=["tpep_pickup_datetime", "tpep_dropoff_datetime"])

    # Keep only Jan 2019
    trips = trips[
        (trips["tpep_pickup_datetime"] >= "2019-01-01") &
        (trips["tpep_pickup_datetime"] <  "2019-02-01")
    ]

    # Remove duplicates
    trips = trips.drop_duplicates(subset=[
        "VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
        "PULocationID", "DOLocationID"
    ])

    # Calculate trip duration in minutes
    trips["trip_duration_min"] = (
        (trips["tpep_dropoff_datetime"] - trips["tpep_pickup_datetime"])
        .dt.total_seconds() / 60
    ).round(2)

    # Logical filters
    trips = trips[trips["trip_duration_min"] > 0]
    trips = trips[trips["trip_duration_min"] < 600]
    trips = trips[trips["trip_distance"]     > 0]
    trips = trips[trips["fare_amount"]       > 0]

    removed = original - len(trips)
    print(f"  Kept {len(trips):,} rows (removed {removed:,}).")

    with open(os.path.join(LOG_DIR, "cleaning_log.txt"), "w") as f:
        f.write(f"Original rows : {original}\n")
        f.write(f"Cleaned rows  : {len(trips)}\n")
        f.write(f"Removed rows  : {removed}\n")

    return trips, original, removed


# ── STEP 3: Feature engineering ───────────────────────────────────────────────

def engineer_features(trips):
    print("Engineering features...")

    trips["avg_speed_mph"] = (
        trips["trip_distance"] / (trips["trip_duration_min"] / 60)
    ).round(2)

    # Remove unrealistic speeds
    before = len(trips)
    trips = trips[
        (trips["avg_speed_mph"] >= 1) &
        (trips["avg_speed_mph"] <= 80)
    ].copy()
    speed_removed = before - len(trips)

    trips["fare_per_mile"] = (
        trips["fare_amount"] / trips["trip_distance"]
    ).round(2)

    # Time features
    trips["pickup_hour"]        = trips["tpep_pickup_datetime"].dt.hour
    trips["pickup_day_of_week"] = trips["tpep_pickup_datetime"].dt.dayofweek
    trips["is_weekend"]         = trips["pickup_day_of_week"].isin([5, 6]).astype(int)

    print(f"  Removed {speed_removed:,} rows with unrealistic speed.")

    with open(os.path.join(LOG_DIR, "cleaning_log.txt"), "a") as f:
        f.write(f"Speed-removed : {speed_removed}\n")
        f.write(f"Final rows    : {len(trips)}\n")

    return trips, speed_removed


# ── STEP 4: Zone lookup ───────────────────────────────────────────────────────

def integrate_lookup(trips, zone_lookup):
    print("Integrating zone lookup...")

    trips = trips.merge(
        zone_lookup, left_on="PULocationID", right_on="LocationID", how="left"
    ).rename(columns={
        "Borough": "PU_Borough", "Zone": "PU_Zone", "service_zone": "PU_ServiceZone"
    }).drop(columns=["LocationID"])

    trips = trips.merge(
        zone_lookup, left_on="DOLocationID", right_on="LocationID", how="left"
    ).rename(columns={
        "Borough": "DO_Borough", "Zone": "DO_Zone", "service_zone": "DO_ServiceZone"
    }).drop(columns=["LocationID"])

    for col in ["PU_Borough", "PU_Zone", "PU_ServiceZone",
                "DO_Borough", "DO_Zone", "DO_ServiceZone"]:
        trips[col] = trips[col].fillna("Unknown")

    print("  Zone lookup done.")
    return trips


# ── STEP 5: Save ──────────────────────────────────────────────────────────────

def save_output(trips):
    out = os.path.join(PROCESSED_DIR, "cleaned_trips.csv")
    trips.to_csv(out, index=False)
    print(f"  Saved {len(trips):,} rows → {out}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    trips, zone_lookup = load_data()
    if trips is None:
        print("Pipeline stopped: missing data files.")
        return

    trips, _, _ = clean_trips(trips)
    trips, _    = engineer_features(trips)
    trips       = integrate_lookup(trips, zone_lookup)
    save_output(trips)

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
