# Release Notes — RouteGuard AI v1.0.0

We are proud to announce the v1.0.0 release of **RouteGuard AI**, a comprehensive, multi-layered Urban Mobility Intelligence & Disaster Decision Support Platform. 

## Key Features

1. **Global Spatial Search & Geocoding**
   - Seamless address search backed by OpenStreetMap's Nominatim geocoder.
   - Panning and re-centering of the Leaflet rendering engine to arbitrary global urban domains.

2. **Traffic-Aware Dynamic Routing**
   - Direct integration of traffic friction weights into the Dijkstra routing calculations in Python.
   - Real-time incident tracking (flooding, road construction, gridlock) with automatic rerouting around closed road segments.

3. **Disaster Simulation & Hazard Overlays**
   - Visual layer support for active wildfire hotspots (NASA FIRMS) and flood warnings (GDACS).
   - Dynamic boundary radius circles indicating affected hazard areas on the GIS map.

4. **AI Mobility Copilot**
   - Interactive glassmorphic conversational assistant integrated into the Next.js frontend.
   - Intelligent command parsing for node ablation queries, bottleneck identification, and emergency routing recommendations.

5. **Multi-City Mock Database Engine**
   - Robust offline backup that seeds in-memory network data for Delhi, Mumbai, Tokyo, New York, and Bengaluru in case MongoDB connection times out.

## Verification & Testing
- **Backend (Jest)**: 3/3 Jest router tests passing.
- **AI/GIS/Graph Engines (Pytest)**: 19/19 Python test suite cases passing.

## Running the Platform
Ensure you run all processes (Gateway backend, Next.js frontend, Python Graph Engine) in separate terminals:
- **Backend Gateway**: `npm run dev` inside `backend/` (running on Port 8000).
- **Frontend Dashboard**: `npm run dev` inside `frontend/` (running on Port 3000).
- **Graph Engine**: `.venv\Scripts\python graph-engine\main.py` (running on Port 8003).
