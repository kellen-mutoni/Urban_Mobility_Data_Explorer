# NYC Urban Mobility Data Explorer

A fullstack web application that explores urban mobility patterns using the **New York City Taxi Trip dataset** (January 2019). Built with Flask, SQLite, and vanilla JavaScript.

## Video Walkthrough
**[Link to Video Walkthrough]** *(https://www.youtube.com/watch?v=pV1qDeYk7YE)*

---

## Project Structure

```
Urban_Mobility_Data_Explorer/
├── backend/
│   ├── app.py                  # Flask API server
│   ├── data_processing.py      # Pipeline orchestrator: DB setup, zone & spatial loading
│   ├── trip_pipeline.py        # Trip data cleaning, feature engineering & DB insertion
│   ├── algorithm.py            # Custom bucket sort implementation
│   ├── db.py                   # Database helpers
│   ├── schema.sql              # SQLite database schema
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── index.html              # Dashboard UI
│   ├── styles.css              # Styling (dark theme, responsive)
│   ├── app.js                  # Frontend entry point
│   ├── charts.js               # Chart.js visualizations
│   ├── map.js                  # Leaflet map & heatmap
│   └── api.js                  # API fetch helpers
├── data/
│   ├── taxi_zone_lookup.csv         # Zone dimension table (included)
│   ├── taxi_zones/                  # Shapefile spatial data (included)
│   └── yellow_tripdata_2019-01.parquet  # Raw trip data (download required, see below)
├── .gitignore
└── README.md
```

``` Architecture diagram
<img width="2600" height="1630" alt="save" src="https://github.com/user-attachments/assets/32cc475f-09db-4f4c-b573-694b9a442440" />

```
> **Generated files** (not in repo, created after running the pipeline):
> `backend/nyc_taxi.db`, `backend/cleaning_log.txt`

---

## Setup Instructions

### Prerequisites
- **Python 3.10+**
- **pip**
- **SQLite** (pre-installed on most systems)
- Internet connection (for CDN libraries: Chart.js, Leaflet)

### Step 1: Clone the Repository
```bash
git clone <your-repo-url>
cd Urban_Mobility_Data_Explorer
```

### Step 2: Download the Trip Dataset
The taxi zone lookup and shapefiles are already included. You only need to download the large trip data file:

```bash
curl -o data/yellow_tripdata_2019-01.parquet \
  "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2019-01.parquet"
```

> The file is ~100MB. It is in Parquet format (faster and smaller than CSV).

### Step 3: Create & Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### Step 4: Install Python Dependencies
```bash
pip install -r backend/requirements.txt
```

Required packages:
| Package | Purpose |
|---------|---------|
| Flask | Web framework |
| Flask-CORS | Cross-origin requests |
| Pandas | Data processing |
| PyArrow | Parquet file reading |
| GeoPandas | Spatial data handling |
| Shapely | Geometry operations |

### Step 5: Run the Data Processing Pipeline
```bash
python3 backend/data_processing.py
```

This will:
- Set up the SQLite database from `schema.sql`
- Load taxi zone lookup and spatial boundary data
- Read and clean 500,000 trip records from the Parquet file (`trip_pipeline.py`)
- Engineer 6 derived features (duration, speed, fare/mile, etc.)
- Write the database to `backend/nyc_taxi.db`
- Write a cleaning report to `backend/cleaning_log.txt`

**Expected time:** ~1 minute

### Step 6: Start the Application
```bash
python3 backend/app.py
```

### Step 7: Open the Dashboard
```
http://localhost:8080
```

---

## Tech Stack
| Component | Technology |
|-----------|-----------|
| Backend | Python / Flask |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Charts | Chart.js |
| Map | Leaflet.js |
| Data Processing | Pandas, PyArrow, GeoPandas |

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/stats` | Overall dataset statistics |
| `GET /api/trips?page=1&borough=Manhattan` | Paginated trips with filters |
| `GET /api/hourly` | Trip counts & avg fare by hour |
| `GET /api/daily` | Trip counts by day of week |
| `GET /api/boroughs` | Stats grouped by pickup borough |
| `GET /api/top-zones?limit=15` | Top pickup/dropoff zones |
| `GET /api/fare-distribution` | Fare distribution buckets |
| `GET /api/zones/geojson` | GeoJSON zone boundaries |
| `GET /api/zone-heatmap` | Pickup counts per zone |
| `GET /api/speed-analysis` | Speed by hour and borough |
| `GET /api/payment-analysis` | Payment type breakdown |
| `GET /api/weekday-vs-weekend` | Weekday vs weekend comparison |
| `GET /api/search?zone=Midtown&sort_by=fare_amount` | Search with custom sort |

---

## Features
- **Data Cleaning Pipeline**: Handles missing values, outliers, date anomalies, and duplicates
- **Feature Engineering**: 6 derived features including trip duration, speed, fare per mile
- **Interactive Filters**: Filter by borough, hour, day, payment type, fare range
- **8+ Visualizations**: Bar charts, line charts, doughnut charts, and more
- **Taxi Zone Heatmap**: Color-coded map showing pickup density across NYC
- **Paginated Trip Table**: Browse individual trip records with full details
- **Custom Algorithm**: Bucket sort implementation (no built-in libraries) for data ordering
- **Responsive Design**: Works on desktop and mobile screens
- **Cleaning Log**: Full transparency on what records were excluded and why

---

## Team Participation Sheet
*https://docs.google.com/spreadsheets/d/16PWaJIwBkJ7Y8JcdZzVxXVtm-uKYBnCeM8ZI48lByoI/edit?usp=sharing*
