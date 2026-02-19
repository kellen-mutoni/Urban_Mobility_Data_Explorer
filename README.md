# NYC Urban Mobility Data Explorer

A fullstack web application for exploring NYC taxi trip patterns across time, borough, zone, and fare — built with Flask, SQLite, and vanilla JavaScript.

## Video Walkthrough
**[Video Walkthrough](https://www.youtube.com/watch?v=pV1qDeYk7YE)*


---

## Project Structure

```
Urban_Mobility_Data_Explorer/
├── backend/
│   ├── app.py               # Flask API (13 endpoints)
│   ├── pipeline.py          # ETL: load → clean → engineer features → join zones
│   ├── load_data_to_sql.py  # Load pipeline output into SQLite
│   ├── algorithm.py         # Custom top-k algorithm (no built-in sort)
│   ├── db.py                # SQLite connection helper
│   ├── schema.sql           # Database schema
│   └── README.md            # API endpoint documentation
├── frontend/
│   ├── index.html           # Dashboard UI
│   ├── styles.css           # Styling
│   ├── app.js               # App entry point and filter logic
│   ├── charts.js            # Chart.js visualizations
│   ├── map.js               # Leaflet choropleth map
│   └── api.js               # API fetch helpers
├── data/
│   ├── taxi_zone_lookup.csv          # Zone dimension table (included)
│   ├── taxi_zones/                   # Shapefile for spatial data (included)
│   └── yellow_tripdata_2019-01.csv   # Raw trip data (download required)
├── requirements.txt
├── .gitignore
└── README.md
```

---
> **Architecture diagram**
<img width="2600" height="1630" alt="save" src="https://github.com/user-attachments/assets/32cc475f-09db-4f4c-b573-694b9a442440" />

---

> **Not in repo** (generated at runtime): `backend/nyc_taxi.db`, `backend/logs/`, `backend/processed/`

---

## Setup

### 1. Clone and enter the repo
```bash
git clone <your-repo-url>
cd Urban_Mobility_Data_Explorer
```

### 2. Download the trip dataset
```bash
curl -o data/yellow_tripdata_2019-01.parquet \
  "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2019-01.parquet"
```
> The pipeline auto-detects parquet or CSV. Parquet is preferred (~100 MB vs ~500 MB for CSV).

### 3. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the ETL pipeline
```bash
python3 backend/pipeline.py
```
Reads raw CSV → cleans → engineers features → writes `backend/processed/cleaned_trips.csv`

### 6. Load data into SQLite
```bash
python3 backend/load_data_to_sql.py
```
Creates `backend/nyc_taxi.db` with all tables and indexes.

### 7. Start the server
```bash
python3 backend/app.py
```

### 8. Open the dashboard
```
http://localhost:8080
```

---

## Tech Stack

| Layer     | Technology                   |
|-----------|------------------------------|
| Backend   | Python, Flask, Flask-CORS    |
| Database  | SQLite                       |
| Frontend  | HTML, CSS, JavaScript        |
| Charts    | Chart.js                     |
| Map       | Leaflet.js                   |
| ETL       | Pandas, GeoPandas            |

---

## API Endpoints

Full documentation in [`backend/README.md`](backend/README.md).

| Endpoint                     | Description                              |
|------------------------------|------------------------------------------|
| `GET /api/stats`             | Overall dataset statistics               |
| `GET /api/trips`             | Paginated trips with filters             |
| `GET /api/top-expensive`     | Top k fares via custom algorithm         |
| `GET /api/hourly`            | Trip counts and avg fare by hour         |
| `GET /api/daily`             | Trip counts by day of week               |
| `GET /api/boroughs`          | Stats grouped by pickup borough          |
| `GET /api/top-zones`         | Top pickup and dropoff zones             |
| `GET /api/fare-distribution` | Fare distribution in $5 buckets          |
| `GET /api/zones/geojson`     | GeoJSON zone boundaries for the map      |
| `GET /api/zone-heatmap`      | Pickup counts per zone                   |
| `GET /api/speed-analysis`    | Avg speed by hour and borough            |
| `GET /api/payment-analysis`  | Payment type breakdown                   |
| `GET /api/weekday-vs-weekend`| Weekday vs weekend comparison            |
| `GET /api/search`            | Filter trips by zone name                |

---

## Custom Algorithm

`backend/algorithm.py` implements a **linear top-k selection** — no `sorted()`, no `sort()`, no `heapq`.
Used by `/api/top-expensive` to return the k highest-fare trips.

- **Time:** O(n × k)
- **Space:** O(n + k)

---

## Team Participation Sheet
*https://docs.google.com/spreadsheets/d/16PWaJIwBkJ7Y8JcdZzVxXVtm-uKYBnCeM8ZI48lByoI/edit?usp=sharing*
