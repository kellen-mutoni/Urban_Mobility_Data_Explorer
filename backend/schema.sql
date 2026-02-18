-- NYC Taxi Trip Database Schema
-- Normalized relational design with proper indexing

-- Dimension table: Taxi Zones
CREATE TABLE IF NOT EXISTS taxi_zones (
    location_id INTEGER PRIMARY KEY,
    borough TEXT NOT NULL,
    zone_name TEXT NOT NULL,
    service_zone TEXT NOT NULL
);

-- Dimension table: Spatial data for zones (GeoJSON boundaries)
CREATE TABLE IF NOT EXISTS taxi_zone_geometries (
    location_id INTEGER PRIMARY KEY,
    geometry_json TEXT,
    FOREIGN KEY (location_id) REFERENCES taxi_zones (location_id)
);

-- Fact table: Cleaned trip records
CREATE TABLE IF NOT EXISTS trips (
    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER,
    pickup_datetime TEXT NOT NULL,
    dropoff_datetime TEXT NOT NULL,
    passenger_count INTEGER,
    trip_distance REAL,
    rate_code_id INTEGER,
    store_and_fwd_flag TEXT,
    pickup_location_id INTEGER NOT NULL,
    dropoff_location_id INTEGER NOT NULL,
    payment_type INTEGER,
    fare_amount REAL,
    extra REAL,
    mta_tax REAL,
    tip_amount REAL,
    tolls_amount REAL,
    improvement_surcharge REAL,
    total_amount REAL,
    congestion_surcharge REAL,
    -- Derived / engineered features
    trip_duration_minutes REAL,
    speed_mph REAL,
    fare_per_mile REAL,
    pickup_hour INTEGER,
    pickup_day_of_week INTEGER,
    is_weekend INTEGER,
    FOREIGN KEY (pickup_location_id) REFERENCES taxi_zones (location_id),
    FOREIGN KEY (dropoff_location_id) REFERENCES taxi_zones (location_id)
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_trips_pickup_datetime ON trips (pickup_datetime);

CREATE INDEX IF NOT EXISTS idx_trips_pickup_location ON trips (pickup_location_id);

CREATE INDEX IF NOT EXISTS idx_trips_dropoff_location ON trips (dropoff_location_id);

CREATE INDEX IF NOT EXISTS idx_trips_pickup_hour ON trips (pickup_hour);

CREATE INDEX IF NOT EXISTS idx_trips_pickup_day ON trips (pickup_day_of_week);

CREATE INDEX IF NOT EXISTS idx_trips_borough_pickup ON trips (
    pickup_location_id,
    pickup_hour
);

CREATE INDEX IF NOT EXISTS idx_trips_fare ON trips (fare_amount);

CREATE INDEX IF NOT EXISTS idx_trips_distance ON trips (trip_distance);