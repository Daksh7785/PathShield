# Project Master Plan — Route Resilience Geospatial Platform

This document serves as the master blueprint for the **Route Resilience** geospatial intelligence platform, detailing the system architecture, implementation roadmap, coding standards, and risk mitigation strategies.

---

## 1. Executive Summary

### What is being built?
An end-to-end, high-performance geospatial data pipeline that:
1.  **Extracts** continuous road network masks from high-resolution satellite imagery (Sentinel-2, Resourcesat LISS-IV, Cartosat-3) under heavy tree canopy, building shadows, and cloud occlusions.
2.  **Reconstructs** these masks into a continuous, weighted node-edge topology (vector graph).
3.  **Analyzes** the network to detect gatekeeper bottlenecks (betweenness centrality) and stress-tests resilience via custom-polygon flood simulation and node-ablation trials.
4.  **Visualizes** findings in a clean, interactive Streamlit/Leaflet web dashboard designed for urban planners and disaster management agencies.

### Why is it superior?
*   **Context-Aware Transformers:** Baseline CNN architectures fail in occluded zones because they lack global receptive fields. Our Vision Transformer (ViT-B/32) models road segments contextually, predicting continuity across 100m+ occluded gaps.
*   **Vector-Directional Healing:** Unlike basic Euclidean nearest-neighbor line drawers, our healing engine uses angular alignment checks to construct natural, valid roadways.
*   **Database Acceleration:** Offloads heavy spatial intersections and bounding box queries to a PostgreSQL + PostGIS database containing spatial indices (GiST).

---

## 2. System Architecture & Decomposition

The project is structured into eight modular, decoupled systems:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SYSTEM DECOMPOSITION                               │
└─────────────────────────────────────────────────────────────────────────────┘
  [System A: Preprocessing & Augmentations]
     └── Normalization (CLAHE) + Occlusion Synthesis (Shadows, Canopy, Clouds)
  [System B: Deep Learning Segmenter]
     └── ViT-B/32 Encoder + Multi-Scale Decoder + Dual Head (Road & Edge Output)
  [System C: Graph Reconstruction & Healing]
     └── Zhang-Suen Thinning + MST & Disjoint Set Angular Gap Healing
  [System D: Spatial Storage Layer]
     └── PostgreSQL + PostGIS (GiST Indexed) + SQLAlchemy Async ORM
  [System E: Backend API Gateway]
     └── FastAPI + Pydantic validation + Redis Caching
  [System F: Analytical Simulation Engine]
     └── Brandes Betweenness Centrality + Shortest Path Routing + Node Ablation
  [System G: Interactive Dashboard]
     └── Streamlit UI + Folium Map Renderer + Live Scenario Toggles
  [System H: MLOps & Quality Assurance]
     └── MLflow logging + pytest unit/integration suite + Docker Compose
```

---

## 3. Directory & Repository Structure

The repository structure matches standard geospatial layouts:

```
route-resilience/
├── README.md
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── requirements-dev.txt
│
├── configs/
│   ├── vit_b32.yaml              # Model hyperparameters
│   └── cities.yaml               # City definitions & bounds
│
├── data/
│   ├── raw/                      # GeoTIFF files (gitignored)
│   ├── processed/                # Tiled image patches (gitignored)
│   └── sample/                   # 100-tile test dataset
│
├── models/
│   ├── vit_segmentation.py       # Encoder-decoder PyTorch architecture
│   ├── attention.py              # Spatial/Channel attention
│   └── losses.py                 # Composite loss functions
│
├── data_pipeline/
│   ├── tiling.py                 # Overlapping patch generation
│   ├── normalization.py          # CLAHE / ImageNet scaling
│   ├── occlusion_synthesis.py    # Perlin shadow/foliage noise
│   └── dataloader.py             # PyTorch Dataset
│
├── topology/
│   ├── skeletonization.py        # Zhang-Suen thinning
│   └── healing.py                # Graph healing engine
│
├── analysis/
│   ├── centrality.py             # Betweenness calculations
│   └── stress_test.py            # Node ablation simulator
│
├── api/
│   ├── main.py                   # FastAPI application factory
│   ├── routers/                  # Network, analysis, export endpoints
│   └── schemas/                  # Pydantic validation models
│
├── database/
│   ├── connection.py             # DB connection pool
│   ├── models.py                 # PostGIS SQL Alchemy tables
│   └── migrations/               # 001_initial_schema.sql
│
├── dashboard/
│   ├── app.py                    # Streamlit dashboard entrypoint
│   └── pages/                    # Sub-pages (Stress test, disaster)
│
└── tests/
    ├── unit/                     # Topology, routing, model tests
    └── conftest.py               # Shared pytest fixtures
```

---

## 4. Coding Standards & Repository Conventions

### A. Coding Conventions
*   **Python Version:** Python 3.11
*   **Style Guide:** Black and PEP-8 compliant. All variables must use `snake_case`, and classes must use `PascalCase`.
*   **Type Hinting:** Mandatory for all functions and class methods.
*   **Documentation:** All public classes and functions must include docstrings in the Google style.

### B. Git & Branching Strategy
*   **Commit Message Convention (Angular style):**
    *   `feat: add spatial attention model`
    *   `fix: resolve edge-case in angular healing`
    *   `docs: update API schemas`
*   **Branch Strategy:**
    *   `main`: Stable production-ready code.
    *   `dev`: Integration branch for developers.
    *   `feature/*`: Feature-specific branches (e.g., `feature/vit-decoder`).

---

## 5. Day-Wise Implementation Roadmap

*   **Day 1 (Hours 0–6): Setup & Database**
    *   Initialize folder scaffold, virtual environment, and Docker container services (PostgreSQL + PostGIS + Redis).
    *   Run initial database migration and seed default city metadata.
*   **Day 1 (Hours 6–12): Data Preprocessing Pipeline**
    *   Write image tiling, CLAHE normalization, and synthetic occlusion augmentation scripts.
    *   Set up PyTorch `RoadSegmentationDataset` and `DataLoader`.
*   **Day 2 (Hours 12–20): DL Architecture & Model Training**
    *   Implement the ViT-B/32 model with attention modules, multi-scale decoders, and composite losses.
    *   Write the training loop and integrate MLflow metrics logging.
*   **Day 2 (Hours 20–26): Topological Graph Reconstruction & Healing**
    *   Implement Zhang-Suen thinning and junction extraction.
    *   Implement Minimum Spanning Tree and Disjoint Set angular-aware gap healing.
    *   Develop betweenness centrality metrics and the node ablation simulation engine.
*   **Day 3 (Hours 26–30): API, Dashboard UI & Testing**
    *   Build FastAPI routers for network routing and simulations.
    *   Assemble the Streamlit interactive dashboard with Folium maps.
    *   Run full test suite (pytest) and package the code.

---

## 6. Risk Analysis & Fallback Plans

| Risk | Impact | Mitigation Plan |
| :--- | :--- | :--- |
| **GPU Out of Memory (OOM) during training** | High | Reduce batch size from 32 to 16/8; freeze ViT backbone and train only the decoder; implement gradient accumulation. |
| **Brandes centrality times out on large graphs** | Medium | Compute centrality on simplified subgraphs; cache calculations in Redis; perform asynchronous calculation via background tasks. |
| **PostGIS installation / driver issues locally** | Medium | Dockerize the PostgreSQL server using preconfigured `postgis/postgis` image; use spatial fallback (SQLite/Spatialite or shapely in memory). |
| **Sentinel-2 imagery resolution too low for micro-streets** | Low | Implement a relaxed IoU buffer (5px) to accommodate alignment offsets; focus evaluation on primary/secondary arterial networks. |
