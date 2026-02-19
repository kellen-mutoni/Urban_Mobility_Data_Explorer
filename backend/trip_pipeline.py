"""
Trip Data Processing Pipeline
------------------------------
Reads the NYC yellow taxi Parquet file in chunks, cleans the data,
engineers features, and inserts records into the SQLite database.
"""

import os
import pandas as pd
import pyarrow.parquet as pq
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

SAMPLE_SIZE = 500000
CHUNK_SIZE = 100000


def clean_and_process_trips(conn, log_file):
    """
    Clean trip data in chunks and insert into database.

    Cleaning rules:
    - Remove rows with missing critical fields (pickup/dropoff times, locations)
    - Remove trips with negative or zero fare
    - Remove trips with unrealistic distance (> 200 miles or 0 for non-zero fare)
    - Remove trips with unrealistic duration (< 1 min or > 12 hours)
    - Remove trips with unrealistic speed (> 80 mph)
    - Remove trips outside January 2019 (data anomalies)
    - Remove duplicate rows
    """
    print("\nStarting trip data cleaning...")
    parquet_path = os.path.join(DATA_DIR, "yellow_tripdata_2019-01.parquet")

    total_raw = 0
    total_cleaned = 0
    total_excluded = 0
    exclusion_reasons = {
        "missing_values": 0,
        "negative_fare": 0,
        "unrealistic_distance": 0,
        "unrealistic_duration": 0,
        "unrealistic_speed": 0,
        "wrong_date_range": 0,
        "duplicates": 0,
        "invalid_location": 0,
        "negative_passengers": 0,
    }

    log_file.write("=" * 60 + "\n")
    log_file.write("NYC TAXI DATA CLEANING LOG\n")
    log_file.write(f"Started: {datetime.now()}\n")
    log_file.write("=" * 60 + "\n\n")

    parquet_file = pq.ParquetFile(parquet_path)
    rows_collected = 0

    for chunk_num, batch in enumerate(parquet_file.iter_batches(batch_size=CHUNK_SIZE)):
        if rows_collected >= SAMPLE_SIZE:
            break

        chunk = batch.to_pandas()
        chunk_start = len(chunk)
        total_raw += chunk_start

        # ---- STEP 1: Handle missing values ----
        critical_cols = [
            "tpep_pickup_datetime",
            "tpep_dropoff_datetime",
            "PULocationID",
            "DOLocationID",
        ]
        before = len(chunk)
        chunk = chunk.dropna(subset=critical_cols)
        exclusion_reasons["missing_values"] += before - len(chunk)

        chunk["passenger_count"] = chunk["passenger_count"].fillna(1)
        chunk["congestion_surcharge"] = chunk["congestion_surcharge"].fillna(0)

        # ---- STEP 2: Parse datetimes ----
        chunk["tpep_pickup_datetime"] = pd.to_datetime(
            chunk["tpep_pickup_datetime"], errors="coerce"
        )
        chunk["tpep_dropoff_datetime"] = pd.to_datetime(
            chunk["tpep_dropoff_datetime"], errors="coerce"
        )
        chunk = chunk.dropna(subset=["tpep_pickup_datetime", "tpep_dropoff_datetime"])

        # ---- STEP 3: Filter date range (Jan 2019 only) ----
        before = len(chunk)
        chunk = chunk[
            (chunk["tpep_pickup_datetime"] >= "2019-01-01")
            & (chunk["tpep_pickup_datetime"] < "2019-02-01")
        ]
        exclusion_reasons["wrong_date_range"] += before - len(chunk)

        # ---- STEP 4: Remove negative/zero fares ----
        before = len(chunk)
        chunk = chunk[chunk["fare_amount"] > 0]
        exclusion_reasons["negative_fare"] += before - len(chunk)

        # ---- STEP 5: Remove unrealistic distances ----
        before = len(chunk)
        chunk = chunk[(chunk["trip_distance"] > 0) & (chunk["trip_distance"] <= 200)]
        exclusion_reasons["unrealistic_distance"] += before - len(chunk)

        # ---- STEP 6: Validate location IDs (1-265) ----
        before = len(chunk)
        chunk = chunk[
            (chunk["PULocationID"] >= 1)
            & (chunk["PULocationID"] <= 265)
            & (chunk["DOLocationID"] >= 1)
            & (chunk["DOLocationID"] <= 265)
        ]
        exclusion_reasons["invalid_location"] += before - len(chunk)

        # ---- STEP 7: Validate passenger count ----
        before = len(chunk)
        chunk = chunk[(chunk["passenger_count"] > 0) & (chunk["passenger_count"] <= 9)]
        exclusion_reasons["negative_passengers"] += before - len(chunk)

        # ---- STEP 8: Remove duplicates ----
        before = len(chunk)
        chunk = chunk.drop_duplicates()
        exclusion_reasons["duplicates"] += before - len(chunk)

        # ---- FEATURE ENGINEERING ----

        chunk["trip_duration_minutes"] = (
            chunk["tpep_dropoff_datetime"] - chunk["tpep_pickup_datetime"]
        ).dt.total_seconds() / 60.0

        before = len(chunk)
        chunk = chunk[
            (chunk["trip_duration_minutes"] >= 1)
            & (chunk["trip_duration_minutes"] <= 720)
        ]
        exclusion_reasons["unrealistic_duration"] += before - len(chunk)

        chunk["speed_mph"] = chunk["trip_distance"] / (
            chunk["trip_duration_minutes"] / 60.0
        )

        before = len(chunk)
        chunk = chunk[chunk["speed_mph"] <= 80]
        exclusion_reasons["unrealistic_speed"] += before - len(chunk)

        chunk["fare_per_mile"] = chunk["fare_amount"] / chunk["trip_distance"]
        chunk["pickup_hour"] = chunk["tpep_pickup_datetime"].dt.hour
        chunk["pickup_day_of_week"] = chunk["tpep_pickup_datetime"].dt.dayofweek
        chunk["is_weekend"] = (chunk["pickup_day_of_week"] >= 5).astype(int)

        # ---- INSERT INTO DATABASE ----
        remaining_needed = SAMPLE_SIZE - rows_collected
        if len(chunk) > remaining_needed:
            chunk = chunk.head(remaining_needed)

        for _, row in chunk.iterrows():
            conn.execute(
                """INSERT INTO trips (
                    vendor_id, pickup_datetime, dropoff_datetime, passenger_count,
                    trip_distance, rate_code_id, store_and_fwd_flag,
                    pickup_location_id, dropoff_location_id, payment_type,
                    fare_amount, extra, mta_tax, tip_amount, tolls_amount,
                    improvement_surcharge, total_amount, congestion_surcharge,
                    trip_duration_minutes, speed_mph, fare_per_mile,
                    pickup_hour, pickup_day_of_week, is_weekend
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    int(row["VendorID"]) if pd.notna(row["VendorID"]) else None,
                    str(row["tpep_pickup_datetime"]),
                    str(row["tpep_dropoff_datetime"]),
                    int(row["passenger_count"]),
                    float(row["trip_distance"]),
                    int(row["RatecodeID"]) if pd.notna(row["RatecodeID"]) else None,
                    str(row["store_and_fwd_flag"]) if pd.notna(row["store_and_fwd_flag"]) else None,
                    int(row["PULocationID"]),
                    int(row["DOLocationID"]),
                    int(row["payment_type"]) if pd.notna(row["payment_type"]) else None,
                    float(row["fare_amount"]),
                    float(row["extra"]) if pd.notna(row["extra"]) else 0,
                    float(row["mta_tax"]) if pd.notna(row["mta_tax"]) else 0,
                    float(row["tip_amount"]) if pd.notna(row["tip_amount"]) else 0,
                    float(row["tolls_amount"]) if pd.notna(row["tolls_amount"]) else 0,
                    float(row["improvement_surcharge"]) if pd.notna(row["improvement_surcharge"]) else 0,
                    float(row["total_amount"]) if pd.notna(row["total_amount"]) else 0,
                    float(row["congestion_surcharge"]) if pd.notna(row["congestion_surcharge"]) else 0,
                    round(float(row["trip_duration_minutes"]), 2),
                    round(float(row["speed_mph"]), 2),
                    round(float(row["fare_per_mile"]), 2),
                    int(row["pickup_hour"]),
                    int(row["pickup_day_of_week"]),
                    int(row["is_weekend"]),
                ),
            )

        rows_collected += len(chunk)
        total_cleaned += len(chunk)
        total_excluded += chunk_start - len(chunk)

        conn.commit()
        print(f"  Chunk {chunk_num + 1}: {chunk_start} raw -> {len(chunk)} clean ({rows_collected}/{SAMPLE_SIZE} collected)")

    # Write cleaning log
    log_file.write(f"Total raw records scanned: {total_raw}\n")
    log_file.write(f"Total records kept (cleaned): {total_cleaned}\n")
    log_file.write(f"Total records excluded: {total_excluded}\n\n")
    log_file.write("Exclusion Breakdown:\n")
    log_file.write("-" * 40 + "\n")
    for reason, count in exclusion_reasons.items():
        log_file.write(f"  {reason}: {count}\n")
    log_file.write("\nCleaning Rules Applied:\n")
    log_file.write("  1. Removed rows missing critical fields (datetime, location IDs)\n")
    log_file.write("  2. Filled missing passenger_count with 1 (assumption: solo rider)\n")
    log_file.write("  3. Filled missing congestion_surcharge with 0\n")
    log_file.write("  4. Filtered to January 2019 only (removed date anomalies)\n")
    log_file.write("  5. Removed trips with fare <= 0\n")
    log_file.write("  6. Removed trips with distance <= 0 or > 200 miles\n")
    log_file.write("  7. Removed trips with invalid location IDs\n")
    log_file.write("  8. Removed trips with invalid passenger count\n")
    log_file.write("  9. Removed duplicate records\n")
    log_file.write("  10. Removed trips with duration < 1 min or > 12 hours\n")
    log_file.write("  11. Removed trips with average speed > 80 mph\n")
    log_file.write(f"\nFeatures Engineered:\n")
    log_file.write("  1. trip_duration_minutes: (dropoff - pickup) in minutes\n")
    log_file.write("  2. speed_mph: distance / (duration in hours)\n")
    log_file.write("  3. fare_per_mile: fare_amount / trip_distance\n")
    log_file.write("  4. pickup_hour: hour extracted from pickup datetime\n")
    log_file.write("  5. pickup_day_of_week: 0=Mon to 6=Sun\n")
    log_file.write("  6. is_weekend: 1 if Saturday/Sunday, 0 otherwise\n")
    log_file.write(f"\nCompleted: {datetime.now()}\n")

    print(f"\nDone! {total_cleaned} clean records inserted into database.")
    print(f"Excluded {total_excluded} records total.")
