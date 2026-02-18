from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import json

from db import get_db
from algorithm import custom_bucket_sort

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

