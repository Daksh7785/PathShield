# RouteGuard AI — Master Execution Plan
## Milestones, Roadmap, and Risk Mitigation Strategy

This document details the step-by-step development roadmap, timelines, and risk mitigation strategies for RouteGuard AI.

---

## 1. Development Milestones & Timeline

```
Milestone 1 (Scaffold) ────> Milestone 2 (Data/AI) ────> Milestone 3 (Backend/GIS) ────> Milestone 4 (Frontend/Sim) ────> Milestone 5 (E2E)
```

1. **Milestone 1: Scaffold & Restructuring (Week 1):**
   - Restructure directories into `frontend`, `backend`, `ai-engine`, `gis-engine`, and `graph-engine`.
   - Setup TS and Python dependency environments.
2. **Milestone 2: Data Ingestion & Model Training (Week 2):**
   - Configure image tiling, CLAHE normalization, and synthetic occlusion overlays.
   - Train ViT-B/32 semantic segmenter and calibrate attention weights.
3. **Milestone 3: Express Backend & GIS Microservice (Week 3):**
   - Connect Express backend to MongoDB and Redis cache.
   - Set up API endpoints for cities and simulations.
4. **Milestone 4: Interactive Dashboard & GIS Leaflet (Week 4):**
   - Build Next.js overview, GIS mapping workbench, and simulation panels.
   - Integrate dynamic route detour calculations.
5. **Milestone 5: Production Deployment & E2E Validation (Week 5):**
   - Configure multi-service Docker Compose and Nginx routing.
   - Run API load tests, Pytest suites, and compile the research package.

---

## 2. Risk Matrix & Mitigation Strategies

| Risk Identified | Impact | Probability | Mitigation Strategy |
| :--- | :---: | :---: | :--- |
| **No Local GPU for Transformer Inference** | High | High | **CPU sliding-window prediction fallback:** Optimizes PyTorch execution on CPU. |
| **Local MongoDB or Redis Connection Refused** | Medium | High | **Embedded Mock Database Fallback:** Express backend automatically switches to local memory mocks to prevent app crashes. |
| **GDAL Binary Compilation Failure on Windows** | High | Medium | **Pure Python Geospatial Libraries:** Replaces raw GDAL with `rasterio` and `shapely` binary wheels, preventing compilation blocks. |
| **Brandes Centrality Bottleneck Latency** | Medium | Medium | **Subgraph Centrality Caching:** Caches calculated centralities in Redis, avoiding recalculating from scratch for unchanged graph sections. |
