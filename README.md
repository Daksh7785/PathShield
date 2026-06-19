<div align="center">

# 🛡️ PathShield
### Route Resilience Intelligence Platform

**A production-grade, AI-powered global digital twin for transportation network resilience analysis and disaster simulation**

[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![OpenStreetMap](https://img.shields.io/badge/OpenStreetMap-Overpass-7EBC6F?style=flat-square&logo=openstreetmap)](https://overpassapi.de)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

🚀 **Live Production Demo**: [https://pathshield-global.vercel.app](https://pathshield-global.vercel.app)

</div>

---

## 🌍 Overview

**PathShield** is a globally scalable, AI-augmented geospatial intelligence system that models, analyzes, and simulates transportation network resilience at planet-Earth scale. It transforms raw road data into a living digital twin — enabling engineers, planners, and emergency responders to understand how road infrastructure behaves under stress, disaster, and failure.

> **Core Philosophy**: Treat the entire Earth as a single connected graph. Any city, any country, any network — dynamically extracted, analyzed, and simulated.

---

## 🎯 Key Capabilities

| Capability | Description |
|-----------|-------------|
| 🌐 **Global Network Extraction** | Dynamically downloads road networks for any location on Earth via OpenStreetMap Overpass API |
| 🧠 **AI Resilience Scoring** | ML-based network analysis using graph-theoretic centrality, betweenness, and connectivity metrics |
| 🌋 **Disaster Simulation** | SIR (Susceptible-Infected-Recovered) epidemic propagation model applied to infrastructure failure cascades |
| 📊 **Shock Index Analysis** | Physics-inspired Shock Index computation to quantify sudden infrastructure load changes |
| 🗺️ **Interactive World Map** | Leaflet-based global map with zoom from world → country → city → road-graph level |
| 🔄 **Self-Healing Networks** | Kruskal's MST-based healing algorithm to restore connectivity after node/edge removal |
| 🌐 **11-Language i18n** | Full international support including RTL languages (Arabic, Hebrew) |
| 📡 **Real-Time Updates** | WebSocket-based live event streaming for disaster propagation timelines |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PATHSHIELD PLATFORM                          │
├────────────┬────────────┬────────────┬────────────┬────────────┤
│  Frontend  │  API       │  AI        │  GIS       │  Graph     │
│  :3000     │  Gateway   │  Engine    │  Engine    │  Engine    │
│            │  :8000     │  :8001     │  :8002     │  :8003     │
│  Next.js   │            │            │            │            │
│  14 +      │  Express   │  FastAPI   │  FastAPI   │  FastAPI   │
│  Leaflet   │  TypeScript│  Python    │  Python    │  Python    │
│            │            │            │            │            │
│  • World   │  • REST    │  • Traffic │  • OSM     │  • Graph   │
│    Map     │    Gateway │    Pred.   │    Extract │    Theory  │
│  • Sim     │  • WebSock │  • AI Risk │  • GeoJSON │  • SIR     │
│    Panel   │  • Auth    │    Score   │  • Network │  • Kruskal │
│  • Charts  │  • MockDB  │  • Anomaly │    Builder │  • Shock   │
│            │            │    Detect  │  • Fallback│    Index   │
└────────────┴────────────┴────────────┴────────────┴────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   OpenStreetMap   │
                    │  Overpass API     │
                    │  (Global Roads)   │
                    └───────────────────┘
```

### Microservices

| Service | Port | Stack | Role |
|---------|------|-------|------|
| **Frontend** | 3000 | Next.js 14, TypeScript, Leaflet.js | Interactive global map UI |
| **API Gateway** | 8000 | Node.js, Express, TypeScript | Request routing, auth, MockDB |
| **AI Engine** | 8001 | Python, FastAPI, scikit-learn | Traffic prediction, risk scoring |
| **GIS Engine** | 8002 | Python, FastAPI, GDAL | OSM extraction, graph building |
| **Graph Engine** | 8003 | Python, FastAPI, NetworkX | Resilience analysis, simulation |

---

## 🧠 Models & Algorithms

### 1. SIR Disaster Propagation Model
Adapted from epidemiology for infrastructure cascading failures:
```
dS/dt = -β·S·I      (Susceptible infrastructure losing capacity)
dI/dt = β·S·I - γ·I (Actively degraded nodes spreading failure)
dR/dt = γ·I          (Recovered/rerouted capacity)
```
- **β (infection rate)**: Mapped from disaster intensity (earthquake magnitude, flood depth)
- **γ (recovery rate)**: Derived from infrastructure redundancy and bypass capacity
- Simulates **how a localized disaster cascades** through the full city road network

### 2. Shock Index
Physics-inspired metric measuring instantaneous load redistribution:
```
SI = ΔTraffic_load / √(Network_capacity × Time_window)
```
Identifies **critical nodes** that absorb disproportionate load when nearby links fail.

### 3. Graph Resilience Index
Composite metric combining:
- **Algebraic connectivity** (Fiedler eigenvalue of the Laplacian)
- **Average betweenness centrality** (bridge node identification)
- **Giant component ratio** (connectivity under random failures)
- **Closeness centrality** distribution (network accessibility)

```
Resilience_Index = 0.4·λ₂ + 0.3·(1 - max_betweenness) + 0.3·GCC_ratio
```

### 4. Kruskal MST Self-Healing
When nodes or edges are removed by disaster simulation:
1. Build residual graph from surviving nodes
2. Run **Kruskal's Minimum Spanning Tree** to find minimum-cost reconnection
3. Proposed healing edges are flagged with `is_healing_edge: true`
4. Visualized on the map as dashed reconstruction routes

### 5. OSM Road Extraction Pipeline
```
User Input (city, bbox)
    ↓
Overpass API Query → Raw OSM GeoJSON (LineString road features)
    ↓
geojson_to_network() → Junction detection via coordinate frequency analysis
    ↓
Haversine distance computation → Real-world edge weights (meters)
    ↓
Node/Edge graph with: type, degree, betweenness, centrality, gateway flags
    ↓
Fallback: Synthetic 8×8 geographic grid if OSM offline/rate-limited
```

### 6. Traffic Anomaly Detection (AI Engine)
- **Isolation Forest** for unsupervised anomaly detection in live traffic streams
- **Linear regression** for short-term congestion forecasting
- Outputs: `congestion_score`, `anomaly_flag`, `predicted_delay_minutes`

---

## 🗺️ Global Coverage

PathShield supports **any location on Earth**:

```bash
# Register any city dynamically
POST /api/v1/cities/osm
{
  "city_name": "Nairobi",
  "bbox": [-1.292, 36.817, -1.275, 36.842]
}
```

**Pre-seeded cities**: Bengaluru, Delhi, Mumbai, New York, Tokyo

**Test-verified continents**: Europe (London), South America (São Paulo), Africa (Cairo), Oceania (Sydney), Eurasia (Moscow)

---

## 📁 Project Structure

```
PathShield/
├── 📄 README.md
├── 📄 CHANGELOG.md
├── 📄 .env.example
├── 📄 .gitignore
├── 📄 docker-compose.yml
├── 📄 Dockerfile.backend
├── 📄 Dockerfile.dashboard
├── 📄 Makefile
├── 📄 requirements.txt
├── 📄 requirements-dev.txt
│
├── 🌐 frontend/                    # Next.js 14 UI
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.tsx           # Landing / dashboard
│   │   │   ├── gis.tsx             # Interactive world map
│   │   │   ├── simulation.tsx      # Disaster simulation panel
│   │   │   ├── rankings.tsx        # City resilience leaderboard
│   │   │   └── marketplace.tsx     # API / data marketplace
│   │   ├── components/
│   │   │   ├── GlobalMap.tsx       # Leaflet world map component
│   │   │   ├── DisasterTimeline.tsx
│   │   │   ├── ResilienceChart.tsx
│   │   │   └── LanguageSelector.tsx
│   │   └── i18n/                   # 11-language translations
│   └── public/
│
├── 🔀 backend/                     # API Gateway (Node.js + TypeScript)
│   └── src/
│       ├── index.ts                # Express server entry point
│       ├── routes/
│       │   ├── cities.ts           # City CRUD + dynamic OSM registration
│       │   ├── simulations.ts      # Disaster simulation endpoints
│       │   ├── traffic.ts          # Live traffic data
│       │   └── marketplace.ts      # API marketplace
│       └── config/
│           └── db.ts               # MongoDB + MockDB fallback
│
├── 🤖 ai-engine/                   # AI/ML Service (Python + FastAPI)
│   └── main.py                     # Traffic prediction, risk scoring
│
├── 🗺️ gis-engine/                  # GIS Processing (Python + FastAPI)
│   ├── main.py                     # OSM extraction, network building
│   └── data_pipeline/
│       ├── osm_rasterizer.py       # Overpass API interface
│       └── tiling.py               # GeoTIFF tiling utilities
│
├── 📊 graph-engine/                # Graph Analysis (Python + FastAPI)
│   ├── main.py                     # SIR simulation, Shock Index
│   └── topology/
│       └── graph_builder.py        # NetworkX graph construction
│
├── 🧪 tests/
│   └── unit/
│       ├── test_gis_engine.py      # GIS + OSM extraction tests
│       └── test_graph_engine.py    # Graph algorithm tests
│
├── 📜 docs/
│   └── reports/                    # Archived analysis reports
│
├── 🚢 deployment/                  # K8s / Helm configs
└── 🔗 shared/                      # Shared schemas and utilities
```

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.11+
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/Daksh7785/PathShield.git
cd PathShield
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys (optional — works without them in mock mode)
```

### 3. Install Dependencies
```bash
# Python dependencies
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt

# Node.js — Backend Gateway
cd backend && npm install && cd ..

# Node.js — Frontend
cd frontend && npm install && cd ..
```

### 4. Start All Services
```bash
# Terminal 1 — Backend Gateway
cd backend && npm run dev

# Terminal 2 — AI Engine
python ai-engine/main.py

# Terminal 3 — GIS Engine
python gis-engine/main.py

# Terminal 4 — Graph Engine
python graph-engine/main.py

# Terminal 5 — Frontend
cd frontend && npm run dev
```

### 5. Access the Platform
| Service | URL |
|---------|-----|
| ⚡ **Live Vercel Production** | **[https://pathshield-global.vercel.app](https://pathshield-global.vercel.app)** |
| 🌐 Frontend Dashboard | http://localhost:3000 |
| 🗺️ GIS Map | http://localhost:3000/gis |
| 🌋 Simulation Panel | http://localhost:3000/simulation |
| 📊 City Rankings | http://localhost:3000/rankings |
| 🔀 API Gateway | http://localhost:8000 |
| 📚 GIS Engine Docs | http://localhost:8002/docs |
| 📚 Graph Engine Docs | http://localhost:8003/docs |

### 6. Docker Compose (All-in-One)
```bash
docker-compose up --build
```

---

## 🔌 API Reference

### Cities

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/cities` | List all registered cities |
| `GET` | `/api/v1/cities/:id` | Get city details + network topology |
| `POST` | `/api/v1/cities/osm` | **Register any global city dynamically** |

#### Register a Global City
```bash
curl -X POST http://localhost:8000/api/v1/cities/osm \
  -H "Content-Type: application/json" \
  -d '{
    "city_name": "Cape Town",
    "bbox": [-33.935, 18.420, -33.915, 18.460]
  }'
```

**Response:**
```json
{
  "id": "cape-town-id",
  "name": "Cape Town",
  "total_nodes": 312,
  "total_edges": 498,
  "network_resilience_index": 0.82,
  "nodes": [...],
  "edges": [...]
}
```

### Simulations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/simulations/:id/stress-test` | Run disaster simulation |
| `POST` | `/api/v1/simulations/:id/route` | Compute resilient routing |
| `GET` | `/api/v1/simulations/feed/disasters` | Live disaster event feed |

#### Run Disaster Simulation
```bash
curl -X POST http://localhost:8000/api/v1/simulations/bengaluru-id/stress-test \
  -H "Content-Type: application/json" \
  -d '{ "disaster_type": "earthquake", "intensity": 7.2 }'
```

### Traffic

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/traffic/:id/congestion` | Live congestion data |

---

## 🌐 Internationalization

PathShield supports **11 languages** with full RTL support:

| Language | Code | Direction |
|----------|------|-----------|
| English | `en` | LTR |
| Hindi | `hi` | LTR |
| Spanish | `es` | LTR |
| French | `fr` | LTR |
| Japanese | `ja` | LTR |
| German | `de` | LTR |
| Portuguese | `pt` | LTR |
| Russian | `ru` | LTR |
| Chinese (Simplified) | `zh` | LTR |
| Arabic | `ar` | **RTL** |
| Hebrew | `he` | **RTL** |

---

## 🧪 Testing

```bash
# Run all unit tests
pytest tests/ -v

# Run specific test suite
pytest tests/unit/test_gis_engine.py -v
pytest tests/unit/test_graph_engine.py -v
```

---

## 📊 Performance Benchmarks

| Metric | Value |
|--------|-------|
| City registration (synthetic grid) | < 1 second |
| City registration (OSM live) | 5–60 seconds (network dependent) |
| SIR simulation (1000 nodes) | < 200ms |
| Shock Index computation | < 50ms |
| API gateway response (P95) | < 30ms |
| Frontend initial load | < 4 seconds |

---

## 🛠️ Technology Stack

### Frontend
- **Next.js 14** — React framework with file-based routing
- **TypeScript** — Type-safe development
- **Leaflet.js** — Interactive map rendering
- **i18next** — Internationalization (11 languages)
- **CSS Modules** — Scoped styling with dark-mode glassmorphism design

### Backend Gateway
- **Node.js + Express** — REST API server
- **TypeScript** — Full type safety
- **Axios** — Service-to-service communication
- **MongoDB / MockDB** — Persistent or in-memory city registry

### AI & Python Services
- **FastAPI** — High-performance async Python APIs
- **NetworkX** — Graph theory algorithms (centrality, MST, connectivity)
- **scikit-learn** — Anomaly detection (Isolation Forest)
- **GDAL / Rasterio** — Geospatial raster processing
- **Requests** — Overpass API calls for OSM road data
- **NumPy / SciPy** — Numerical computation for physics models

### Infrastructure
- **Docker + Docker Compose** — Containerized deployment
- **Git** — Version control

---

## 📈 Roadmap

- [ ] **Real-time Overpass API streaming** with tile-based incremental loading
- [ ] **PostgreSQL + PostGIS** production database integration
- [ ] **Satellite imagery integration** via Sentinel-2 / Landsat for road occlusion detection
- [ ] **Deep learning road extraction** (U-Net / SegFormer) from satellite tiles
- [ ] **Cross-border corridor analysis** — multi-country routing
- [ ] **Maritime and air transport** dependency modeling
- [ ] **Multi-disaster scenario stacking** (flood + earthquake simultaneous)
- [ ] **WebGL-accelerated map rendering** for 10M+ node networks

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built with ❤️ for a more resilient world**

*PathShield — Because infrastructure resilience is not optional.*

</div>