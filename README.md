# Route Resilience — Urban Mobility Geospatial Intelligence Platform

Route Resilience is an end-to-end geospatial intelligence pipeline designed to extract robust, continuous road network vector topologies from high-resolution satellite imagery under heavy occlusions (foliage, building shadows, clouds) and perform graph-theoretic structural stress testing.

---

## 1. System Overview

```
 🛰️ Satellite Image (Cartosat-3/Sentinel-2)
             │
             ▼
   [ Data Preprocessing ]  <--- CLAHE & Overlapping Tiling
             │
             ▼
   [ Vision Transformer ]  <--- Global Self-Attention Segmenter
             │
             ▼
   [ Skeleton & Healing ]  <--- Zhang-Suen Thinning + MST Angular Healing
             │
             ▼
    [ Database Storage ]  <--- PostgreSQL + PostGIS Indexing
             │
             ▼
     [ API Backend ]      <--- FastAPI (Shortest Paths, Ablations)
             │
             ▼
   [ Planner Dashboard ]  <--- Streamlit (Folium / Interactive GIS maps)
```

---

## 2. Tech Stack

- **Deep Learning:** PyTorch, timm (Vision Transformer backbone)
- **Topological Reconstruction:** OpenCV, Scikit-Image, NetworkX
- **Geospatial Processing:** GDAL, Rasterio, GeoPandas, Shapely
- **Database:** PostgreSQL + PostGIS, Redis
- **APIs:** FastAPI, Uvicorn, SQLAlchemy (Async)
- **Dashboard:** Streamlit, Folium, Plotly

---

## 3. Quick Start

### Prerequisites
Make sure Docker and Docker Compose are installed.

### 1. Build and Launch Containers
```bash
docker-compose up --build -d
```

### 2. Initialize and Seed Database
```bash
docker-compose exec backend python scripts/seed_database.py
```

### 3. Generate Mock Demo Data and Preprocess
```bash
docker-compose exec backend python scripts/demo_setup.py
```

### 4. Access Services
- **Streamlit Dashboard:** `http://localhost:8501`
- **FastAPI Documentation:** `http://localhost:8000/docs`