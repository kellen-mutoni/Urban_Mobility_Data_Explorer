"""
Data Processing Orchestrator
------------------------------
Sets up the database, loads taxi zone and spatial data,
then delegates trip processing to trip_pipeline.py.
"""

import pandas as pd
import sqlite3
import os
import json
import time

from trip_pipeline import clean_and_process_trips

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "backend", "nyc_taxi.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "backend", "schema.sql")
LOG_PATH = os.path.join(BASE_DIR, "backend", "cleaning_log.txt")


def setup_database():
    """Create database tables from schema file."""
    print("Setting up database...")
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database tables created.")


def load_taxi_zones(conn):
    """Load taxi zone lookup data into the database."""
    print("Loading taxi zones...")
    zones_path = os.path.join(DATA_DIR, "taxi_zone_lookup.csv")
    zones_df = pd.read_csv(zones_path)

    for _, row in zones_df.iterrows():
        loc_id = int(row["LocationID"])
        borough = str(row["Borough"]) if pd.notna(row["Borough"]) else "Unknown"
        zone = str(row["Zone"]) if pd.notna(row["Zone"]) else "Unknown"
        service = str(row["service_zone"]) if pd.notna(row["service_zone"]) else "Unknown"

        conn.execute(
            "INSERT OR REPLACE INTO taxi_zones (location_id, borough, zone_name, service_zone) VALUES (?, ?, ?, ?)",
            (loc_id, borough, zone, service),
        )

    conn.commit()
    print(f"Loaded {len(zones_df)} taxi zones.")


def load_spatial_data(conn):
    """Load spatial boundary data from shapefiles and store as GeoJSON."""
    print("Loading spatial data...")
    try:
        import geopandas as gpd

        shp_path = os.path.join(DATA_DIR, "taxi_zones", "taxi_zones.shp")
        gdf = gpd.read_file(shp_path)

        # Convert to WGS84 (lat/lon) for web mapping
        gdf = gdf.to_crs(epsg=4326)

        count = 0
        for _, row in gdf.iterrows():
            loc_id = int(row["LocationID"]) if "LocationID" in row else int(row["OBJECTID"])
            geom_json = row["geometry"].__geo_interface__
            conn.execute(
                "INSERT OR REPLACE INTO taxi_zone_geometries (location_id, geometry_json) VALUES (?, ?)",
                (loc_id, json.dumps(geom_json)),
            )
            count += 1

        conn.commit()
        print(f"Loaded {count} zone geometries.")
    except Exception as e:
        print(f"Warning: Could not load spatial data: {e}")
        print("Continuing without spatial data...")


def main():
    """Run the full data processing pipeline."""
    start_time = time.time()
    print("=" * 50)
    print("NYC TAXI DATA PROCESSING PIPELINE")
    print("=" * 50)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed old database.")

    setup_database()
    conn = sqlite3.connect(DB_PATH)
    log_file = open(LOG_PATH, "w")

    try:
        load_taxi_zones(conn)
        load_spatial_data(conn)
        clean_and_process_trips(conn, log_file)
    finally:
        log_file.close()
        conn.close()

    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.1f} seconds")
    print(f"Database saved to: {DB_PATH}")
    print(f"Cleaning log saved to: {LOG_PATH}")


if __name__ == "__main__":
    main()
