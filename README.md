# NYC Urban Mobility Data Explorer

A fullstack web application that explores urban mobility patterns using the **New York City Taxi Trip dataset** (January 2019). Built with Flask, SQLite, and vanilla JavaScript.

## Video Walkthrough
**[Link to Video Walkthrough]** *(Add your video link here)*

---

## Project Structure

```
Urban Mobility Data Explorer/
├── backend/
│   ├── app.py                  # Flask API server (serves both API and frontend)
│   ├── data_processing.py      # Data cleaning & feature engineering pipeline
│   ├── schema.sql              # SQLite database schema
│   ├── requirements.txt        # Python dependencies
│   ├── cleaning_log.txt        # Log of excluded/suspicious records
│   └── nyc_taxi.db             # SQLite database (generated after processing)
├── frontend/
│   ├── index.html              # Dashboard UI
│   ├── styles.css              # Styling (dark theme, responsive)
│   └── app.js                  # Frontend logic (charts, map, table)
├── data/
│   ├── yellow_tripdata_2019-01.csv  # Raw trip data (download required)
│   ├── taxi_zone_lookup.csv         # Zone dimension table
│   └── taxi_zones/                  # Shapefile spatial data (extracted from zip)
├── .gitignore
└── README.md
```

---

## Setup Instructions

### Prerequisites
- **Python 3.10+** installed
- **pip** package manager
- **SQLite** (comes pre-installed on most systems)
- An internet connection (for CDN libraries: Chart.js, Leaflet)

### Step 1: Clone the Repository
```bash
git clone <your-repo-url>
cd "Urban Mobility Data Explorer"
```

### Step 2: Download the Dataset
Download the following files and place them in the `data/` folder:
1. **yellow_tripdata_2019-01.csv** (Fact Table) - [Download from TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) or use the provided link from the assignment.
2. **taxi_zone_lookup.csv** (Dimension Table) - Should already be in the project
3. **taxi_zones.zip** (Spatial Metadata) - Extract into `data/taxi_zones/`

If the taxi_zones.zip hasn't been extracted yet:
```bash
unzip taxi_zones.zip -d data/taxi_zones/
```

### Step 3: Install Python Dependencies
```bash
pip install -r backend/requirements.txt
```

The required packages are:
- Flask (web framework)
- Flask-CORS (cross-origin requests)
- Pandas (data processing)
- GeoPandas (spatial data handling)
- Shapely (geometry operations)

### Step 4: Run the Data Processing Pipeline
This cleans the raw data, engineers features, and loads everything into SQLite:
```bash
python3 backend/data_processing.py
```
This will:
- Load and clean 500,000 trip records from the raw CSV
- Handle missing values, outliers, and anomalies
- Engineer 6 derived features (duration, speed, fare/mile, etc.)
- Load taxi zone lookup and spatial boundary data
- Create the SQLite database at `backend/nyc_taxi.db`
- Generate a cleaning log at `backend/cleaning_log.txt`

**Expected time:** ~1 minute

### Step 5: Start the Application
```bash
python3 backend/app.py
```

### Step 6: Open the Dashboard
Open your browser and go to:
```
http://localhost:8080
```

The dashboard loads everything from the Flask API. You should see:
- Summary statistics cards
- Interactive charts (hourly patterns, borough breakdown, fare distribution, etc.)
- A zoomable taxi zone heatmap
- A filterable, paginated trip records table

---

## Tech Stack
| Component | Technology |
|-----------|-----------|
| Backend | Python / Flask |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Charts | Chart.js |
| Map | Leaflet.js |
| Data Processing | Pandas, GeoPandas |

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
*(Add link to your team participation sheet here)*
