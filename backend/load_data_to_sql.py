"""
Load Cleaned Data into SQLite
------------------------------
Run pipeline.py first to generate processed/cleaned_trips.csv.
Then run this script to populate the SQLite database.

Usage:
    python pipeline.py
    python load_data_to_sql.py
"""

import sqlite3
import pandas as pd
import os
import json

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DB_PATH       = os.path.join(BASE_DIR, "nyc_taxi.db")
SCHEMA_PATH   = os.path.join(BASE_DIR, "schema.sql")
PROCESSED_CSV = os.path.join(BASE_DIR, "processed", "cleaned_trips.csv")
ZONES_CSV     = os.path.join(BASE_DIR, "..", "data", "taxi_zone_lookup.csv")
GEOJSON_PATH  = os.path.join(BASE_DIR, "processed", "taxi_zones.geojson")


def create_tables(conn):
    print("Creating tables...")
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    print("  Tables ready.")


def load_zones(conn):
    print("Loading taxi zones...")
    zones = pd.read_csv(ZONES_CSV)
    zones.columns = [c.strip() for c in zones.columns]

    for _, row in zones.iterrows():
        conn.execute(
            """INSERT OR IGNORE INTO taxi_zones (location_id, borough, zone_name, service_zone)
               VALUES (?, ?, ?, ?)""",
            (int(row["LocationID"]), str(row["Borough"]),
             str(row["Zone"]), str(row["service_zone"]))
        )

    # Load GeoJSON geometries if available
    if os.path.exists(GEOJSON_PATH):
        with open(GEOJSON_PATH) as f:
            gj = json.load(f)
        for feature in gj.get("features", []):
            loc_id = feature["properties"].get("LocationID")
            geom   = json.dumps(feature["geometry"])
            if loc_id:
                conn.execute(
                    """INSERT OR IGNORE INTO taxi_zone_geometries (location_id, geometry_json)
                       VALUES (?, ?)""",
                    (int(loc_id), geom)
                )

    conn.commit()
    print(f"  Loaded {conn.execute('SELECT COUNT(*) FROM taxi_zones').fetchone()[0]} zones.")


def load_trips(conn):
    print("Loading trips...")
    if not os.path.exists(PROCESSED_CSV):
        print("  ERROR: processed/cleaned_trips.csv not found. Run pipeline.py first.")
        return

    trips = pd.read_csv(PROCESSED_CSV)

    # Rename columns to match schema
    col_map = {
        "VendorID":              "vendor_id",
        "tpep_pickup_datetime":  "pickup_datetime",
        "tpep_dropoff_datetime": "dropoff_datetime",
        "passenger_count":       "passenger_count",
        "trip_distance":         "trip_distance",
        "RatecodeID":            "rate_code_id",
        "store_and_fwd_flag":    "store_and_fwd_flag",
        "PULocationID":          "pickup_location_id",
        "DOLocationID":          "dropoff_location_id",
        "payment_type":          "payment_type",
        "fare_amount":           "fare_amount",
        "extra":                 "extra",
        "mta_tax":               "mta_tax",
        "tip_amount":            "tip_amount",
        "tolls_amount":          "tolls_amount",
        "improvement_surcharge": "improvement_surcharge",
        "total_amount":          "total_amount",
        "trip_duration_min":     "trip_duration_minutes",
        "avg_speed_mph":         "speed_mph",
        "fare_per_mile":         "fare_per_mile",
        "pickup_hour":           "pickup_hour",
        "pickup_day_of_week":    "pickup_day_of_week",
        "is_weekend":            "is_weekend",
    }
    trips = trips.rename(columns=col_map)

    keep = [v for v in col_map.values() if v in trips.columns]
    trips = trips[keep]

    trips.to_sql("trips", conn, if_exists="append", index=False, chunksize=5000)
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    print(f"  Loaded {total:,} trips into SQLite.")


def main():
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    load_zones(conn)
    load_trips(conn)
    conn.close()
    print("Database ready.")


if __name__ == "__main__":
    main()
