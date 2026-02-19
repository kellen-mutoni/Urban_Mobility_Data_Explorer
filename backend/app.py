"""
Flask Backend API for NYC Taxi Data Explorer
----------------------------------------------
Endpoints:
- GET /api/stats               -> Overall dataset statistics
- GET /api/trips               -> Paginated trips with filters
- GET /api/hourly              -> Trip counts & avg fare by hour
- GET /api/daily               -> Trip counts by day of week
- GET /api/boroughs            -> Trip stats grouped by borough
- GET /api/top-zones           -> Top pickup/dropoff zones
- GET /api/fare-distribution   -> Fare amount distribution buckets
- GET /api/zones/geojson       -> GeoJSON for all taxi zones
- GET /api/zone-heatmap        -> Pickup counts per zone (for map)
- GET /api/speed-analysis      -> Speed patterns by hour and borough
- GET /api/payment-analysis    -> Payment type breakdown
- GET /api/weekday-vs-weekend  -> Weekday vs weekend comparison
- GET /api/search              -> Filter trips by zone name
- GET /api/top-expensive       -> Top k trips by fare (uses custom algorithm)
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import json

from db import get_db
from algorithm import top_k_fares

app = Flask(__name__)
CORS(app)

# Serve frontend files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


@app.route("/")
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# =========================================================
#  API ENDPOINTS
# =========================================================

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get overall dataset statistics."""
    conn = get_db()
    stats = {}

    row = conn.execute("SELECT COUNT(*) as cnt FROM trips").fetchone()
    stats["total_trips"] = row["cnt"]

    row = conn.execute(
        """SELECT
            AVG(trip_distance) as avg_distance,
            AVG(trip_duration_minutes) as avg_duration,
            AVG(fare_amount) as avg_fare,
            AVG(speed_mph) as avg_speed,
            AVG(tip_amount) as avg_tip,
            AVG(total_amount) as avg_total,
            SUM(total_amount) as total_revenue,
            AVG(passenger_count) as avg_passengers
        FROM trips"""
    ).fetchone()
    stats["avg_distance"] = round(row["avg_distance"], 2)
    stats["avg_duration"] = round(row["avg_duration"], 2)
    stats["avg_fare"] = round(row["avg_fare"], 2)
    stats["avg_speed"] = round(row["avg_speed"], 2)
    stats["avg_tip"] = round(row["avg_tip"], 2)
    stats["avg_total"] = round(row["avg_total"], 2)
    stats["total_revenue"] = round(row["total_revenue"], 2)
    stats["avg_passengers"] = round(row["avg_passengers"], 2)

    row = conn.execute(
        "SELECT COUNT(DISTINCT pickup_location_id) as zones FROM trips"
    ).fetchone()
    stats["active_zones"] = row["zones"]

    conn.close()
    return jsonify(stats)


@app.route("/api/trips", methods=["GET"])
def get_trips():
    """Get paginated trips with optional filters."""
    conn = get_db()

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    offset = (page - 1) * per_page

    # Build filter conditions
    conditions = []
    params = []

    borough = request.args.get("borough")
    if borough:
        conditions.append(
            "pickup_location_id IN (SELECT location_id FROM taxi_zones WHERE borough = ?)"
        )
        params.append(borough)

    min_fare = request.args.get("min_fare")
    if min_fare:
        conditions.append("fare_amount >= ?")
        params.append(float(min_fare))

    max_fare = request.args.get("max_fare")
    if max_fare:
        conditions.append("fare_amount <= ?")
        params.append(float(max_fare))

    min_distance = request.args.get("min_distance")
    if min_distance:
        conditions.append("trip_distance >= ?")
        params.append(float(min_distance))

    max_distance = request.args.get("max_distance")
    if max_distance:
        conditions.append("trip_distance <= ?")
        params.append(float(max_distance))

    hour = request.args.get("hour")
    if hour:
        conditions.append("pickup_hour = ?")
        params.append(int(hour))

    day = request.args.get("day")
    if day:
        conditions.append("pickup_day_of_week = ?")
        params.append(int(day))

    payment = request.args.get("payment_type")
    if payment:
        conditions.append("payment_type = ?")
        params.append(int(payment))

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Get total count for pagination
    count_query = f"SELECT COUNT(*) as cnt FROM trips WHERE {where_clause}"
    total = conn.execute(count_query, params).fetchone()["cnt"]

    # Get trips with zone names
    query = f"""
        SELECT t.*,
            pz.zone_name as pickup_zone, pz.borough as pickup_borough,
            dz.zone_name as dropoff_zone, dz.borough as dropoff_borough
        FROM trips t
        LEFT JOIN taxi_zones pz ON t.pickup_location_id = pz.location_id
        LEFT JOIN taxi_zones dz ON t.dropoff_location_id = dz.location_id
        WHERE {where_clause}
        ORDER BY t.pickup_datetime DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])
    rows = conn.execute(query, params).fetchall()

    trips = [dict(row) for row in rows]
    conn.close()

    return jsonify(
        {
            "trips": trips,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }
    )


@app.route("/api/hourly", methods=["GET"])
def get_hourly():
    """Trip counts and average fare by hour of day."""
    conn = get_db()
    rows = conn.execute(
        """SELECT pickup_hour as hour,
            COUNT(*) as trip_count,
            AVG(fare_amount) as avg_fare,
            AVG(trip_duration_minutes) as avg_duration,
            AVG(speed_mph) as avg_speed,
            AVG(tip_amount) as avg_tip
        FROM trips
        GROUP BY pickup_hour
        ORDER BY pickup_hour"""
    ).fetchall()
    conn.close()

    data = []
    for row in rows:
        data.append(
            {
                "hour": row["hour"],
                "trip_count": row["trip_count"],
                "avg_fare": round(row["avg_fare"], 2),
                "avg_duration": round(row["avg_duration"], 2),
                "avg_speed": round(row["avg_speed"], 2),
                "avg_tip": round(row["avg_tip"], 2),
            }
        )
    return jsonify(data)


@app.route("/api/daily", methods=["GET"])
def get_daily():
    """Trip counts by day of the week."""
    conn = get_db()
    rows = conn.execute(
        """SELECT pickup_day_of_week as day,
            COUNT(*) as trip_count,
            AVG(fare_amount) as avg_fare,
            AVG(trip_distance) as avg_distance,
            SUM(CASE WHEN is_weekend = 1 THEN 1 ELSE 0 END) as weekend_trips
        FROM trips
        GROUP BY pickup_day_of_week
        ORDER BY pickup_day_of_week"""
    ).fetchall()
    conn.close()

    day_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    data = []
    for row in rows:
        data.append(
            {
                "day": row["day"],
                "day_name": day_names[row["day"]],
                "trip_count": row["trip_count"],
                "avg_fare": round(row["avg_fare"], 2),
                "avg_distance": round(row["avg_distance"], 2),
            }
        )
    return jsonify(data)


@app.route("/api/boroughs", methods=["GET"])
def get_boroughs():
    """Trip stats grouped by pickup borough."""
    conn = get_db()
    rows = conn.execute(
        """SELECT z.borough,
            COUNT(*) as trip_count,
            AVG(t.fare_amount) as avg_fare,
            AVG(t.trip_distance) as avg_distance,
            AVG(t.trip_duration_minutes) as avg_duration,
            AVG(t.speed_mph) as avg_speed,
            AVG(t.tip_amount) as avg_tip,
            SUM(t.total_amount) as total_revenue
        FROM trips t
        JOIN taxi_zones z ON t.pickup_location_id = z.location_id
        GROUP BY z.borough
        ORDER BY trip_count DESC"""
    ).fetchall()
    conn.close()

    data = []
    for row in rows:
        data.append(
            {
                "borough": row["borough"],
                "trip_count": row["trip_count"],
                "avg_fare": round(row["avg_fare"], 2),
                "avg_distance": round(row["avg_distance"], 2),
                "avg_duration": round(row["avg_duration"], 2),
                "avg_speed": round(row["avg_speed"], 2),
                "avg_tip": round(row["avg_tip"], 2),
                "total_revenue": round(row["total_revenue"], 2),
            }
        )
    return jsonify(data)


@app.route("/api/top-zones", methods=["GET"])
def get_top_zones():
    """Top pickup and dropoff zones."""
    conn = get_db()
    limit = int(request.args.get("limit", 15))

    # Top pickup zones
    pickup_rows = conn.execute(
        """SELECT z.zone_name, z.borough, COUNT(*) as trip_count
        FROM trips t
        JOIN taxi_zones z ON t.pickup_location_id = z.location_id
        GROUP BY t.pickup_location_id
        ORDER BY trip_count DESC
        LIMIT ?""",
        (limit,),
    ).fetchall()

    # Top dropoff zones
    dropoff_rows = conn.execute(
        """SELECT z.zone_name, z.borough, COUNT(*) as trip_count
        FROM trips t
        JOIN taxi_zones z ON t.dropoff_location_id = z.location_id
        GROUP BY t.dropoff_location_id
        ORDER BY trip_count DESC
        LIMIT ?""",
        (limit,),
    ).fetchall()

    conn.close()

    return jsonify(
        {
            "top_pickup": [dict(r) for r in pickup_rows],
            "top_dropoff": [dict(r) for r in dropoff_rows],
        }
    )


@app.route("/api/fare-distribution", methods=["GET"])
def get_fare_distribution():
    """Fare amount distribution buckets, ordered by fare range."""
    conn = get_db()

    rows = conn.execute(
        """SELECT
            CAST(fare_amount / 5 AS INT) * 5 as bucket_start,
            COUNT(*) as count,
            AVG(fare_amount) as avg_fare
        FROM trips
        WHERE fare_amount > 0 AND fare_amount <= 100
        GROUP BY CAST(fare_amount / 5 AS INT)
        ORDER BY bucket_start"""
    ).fetchall()
    conn.close()

    data = []
    for row in rows:
        start = int(row["bucket_start"])
        data.append({
            "range": f"${start}-${start + 5}",
            "count": row["count"],
            "avg_fare": round(row["avg_fare"], 2),
        })

    return jsonify(data)


@app.route("/api/zones/geojson", methods=["GET"])
def get_zones_geojson():
    """Get GeoJSON for all taxi zones (for map rendering)."""
    conn = get_db()
    rows = conn.execute(
        """SELECT g.location_id, g.geometry_json, z.zone_name, z.borough, z.service_zone
        FROM taxi_zone_geometries g
        JOIN taxi_zones z ON g.location_id = z.location_id"""
    ).fetchall()

    features = []
    for row in rows:
        feature = {
            "type": "Feature",
            "properties": {
                "location_id": row["location_id"],
                "zone_name": row["zone_name"],
                "borough": row["borough"],
                "service_zone": row["service_zone"],
            },
            "geometry": json.loads(row["geometry_json"]),
        }
        features.append(feature)

    conn.close()
    return jsonify({"type": "FeatureCollection", "features": features})


@app.route("/api/zone-heatmap", methods=["GET"])
def get_zone_heatmap():
    """Pickup counts per zone for heatmap visualization."""
    conn = get_db()
    rows = conn.execute(
        """SELECT t.pickup_location_id as location_id,
            z.zone_name, z.borough,
            COUNT(*) as pickup_count,
            AVG(t.fare_amount) as avg_fare
        FROM trips t
        JOIN taxi_zones z ON t.pickup_location_id = z.location_id
        GROUP BY t.pickup_location_id
        ORDER BY pickup_count DESC"""
    ).fetchall()
    conn.close()

    data = []
    for row in rows:
        data.append(
            {
                "location_id": row["location_id"],
                "zone_name": row["zone_name"],
                "borough": row["borough"],
                "pickup_count": row["pickup_count"],
                "avg_fare": round(row["avg_fare"], 2),
            }
        )
    return jsonify(data)


@app.route("/api/speed-analysis", methods=["GET"])
def get_speed_analysis():
    """Speed patterns by hour and borough."""
    conn = get_db()
    rows = conn.execute(
        """SELECT z.borough, t.pickup_hour as hour,
            AVG(t.speed_mph) as avg_speed,
            COUNT(*) as trip_count
        FROM trips t
        JOIN taxi_zones z ON t.pickup_location_id = z.location_id
        WHERE z.borough IN ('Manhattan', 'Brooklyn', 'Queens', 'Bronx')
        GROUP BY z.borough, t.pickup_hour
        ORDER BY z.borough, t.pickup_hour"""
    ).fetchall()
    conn.close()

    data = [dict(r) for r in rows]
    for d in data:
        d["avg_speed"] = round(d["avg_speed"], 2)
    return jsonify(data)


@app.route("/api/search", methods=["GET"])
def search_trips():
    """
    Search/filter trips using custom bucket sort for results.
    Allows searching by zone name and sorting results.
    """
    conn = get_db()
    zone_query = request.args.get("zone", "")
    sort_by = request.args.get("sort_by", "fare_amount")
    limit = int(request.args.get("limit", 100))

    valid_sort_fields = [
        "fare_amount", "trip_distance", "trip_duration_minutes",
        "speed_mph", "total_amount", "tip_amount"
    ]
    if sort_by not in valid_sort_fields:
        sort_by = "fare_amount"

    query = """
        SELECT t.trip_id, t.fare_amount, t.trip_distance, t.trip_duration_minutes,
            t.speed_mph, t.total_amount, t.tip_amount, t.pickup_hour,
            pz.zone_name as pickup_zone, pz.borough as pickup_borough,
            dz.zone_name as dropoff_zone, dz.borough as dropoff_borough
        FROM trips t
        JOIN taxi_zones pz ON t.pickup_location_id = pz.location_id
        JOIN taxi_zones dz ON t.dropoff_location_id = dz.location_id
    """
    params = []

    if zone_query:
        query += " WHERE (pz.zone_name LIKE ? OR dz.zone_name LIKE ?)"
        params.extend([f"%{zone_query}%", f"%{zone_query}%"])

    query += f" LIMIT {limit}"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    data = [dict(r) for r in rows]

    return jsonify(data)


@app.route("/api/top-expensive", methods=["GET"])
def top_expensive():
    """Return the k most expensive trips using the custom top-k algorithm."""
    k = int(request.args.get("k", 10))

    conn = get_db()
    rows = conn.execute(
        """SELECT trip_id, fare_amount, trip_distance, trip_duration_minutes,
               pickup_hour, pickup_location_id, dropoff_location_id
           FROM trips
           LIMIT 1000"""
    ).fetchall()
    conn.close()

    trips = [dict(r) for r in rows]
    result = top_k_fares(trips, k=k)

    return jsonify(result)


@app.route("/api/payment-analysis", methods=["GET"])
def get_payment_analysis():
    """Payment type breakdown."""
    conn = get_db()
    rows = conn.execute(
        """SELECT payment_type,
            COUNT(*) as trip_count,
            AVG(fare_amount) as avg_fare,
            AVG(tip_amount) as avg_tip,
            SUM(total_amount) as total_revenue
        FROM trips
        GROUP BY payment_type
        ORDER BY trip_count DESC"""
    ).fetchall()
    conn.close()

    payment_names = {
        1: "Credit Card",
        2: "Cash",
        3: "No Charge",
        4: "Dispute",
        5: "Unknown",
        6: "Voided",
    }

    data = []
    for row in rows:
        pt = row["payment_type"]
        data.append(
            {
                "payment_type": pt,
                "payment_name": payment_names.get(pt, f"Type {pt}"),
                "trip_count": row["trip_count"],
                "avg_fare": round(row["avg_fare"], 2),
                "avg_tip": round(row["avg_tip"], 2),
                "total_revenue": round(row["total_revenue"], 2),
            }
        )
    return jsonify(data)


@app.route("/api/weekday-vs-weekend", methods=["GET"])
def weekday_vs_weekend():
    """Compare weekday vs weekend trip patterns."""
    conn = get_db()
    rows = conn.execute(
        """SELECT
            CASE WHEN is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END as period,
            COUNT(*) as trip_count,
            AVG(fare_amount) as avg_fare,
            AVG(trip_distance) as avg_distance,
            AVG(trip_duration_minutes) as avg_duration,
            AVG(speed_mph) as avg_speed,
            AVG(tip_amount) as avg_tip
        FROM trips
        GROUP BY is_weekend"""
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    print("Starting NYC Taxi Data Explorer API...")
    print("API running at http://localhost:8080")
    app.run(debug=True, port=8080)
