# RouteGuard AI — Repository Plan
## Folder Scaffold, Coding Standards, and Testing Architecture

This document describes the repository layout and conventions for development on RouteGuard AI.

---

## 1. Directory Structure

```
RouteGuard-AI/
├── frontend/             # Next.js Client Dashboard
│   ├── public/           # Static assets (icons, maps)
│   └── src/
│       ├── components/   # MapComponent, sidebar controls
│       ├── pages/        # index.tsx, gis.tsx, simulation.tsx
│       └── styles/       # globals.css
├── backend/              # Node.js Express Gateway
│   └── src/
│       ├── config/       # db.ts (MongoDB/mock connector)
│       ├── models/       # City.ts Mongoose Schema
│       ├── routes/       # cities.ts, simulations.ts
│       └── server.ts     # Express/Socket.IO server
├── ai-engine/            # PyTorch segmentation service
│   ├── models/           # vit_segmentation.py
│   ├── inference/        # predictor.py
│   └── main.py           # FastAPI prediction API
├── gis-engine/           # Rasterio / GeoPandas service
│   ├── data_pipeline/    # tiling.py, normalization.py
│   └── main.py           # FastAPI tiling API
├── graph-engine/         # NetworkX topology service
│   ├── topology/         # skeletonization.py, healing.py
│   ├── analysis/         # centrality.py, stress_test.py, routing.py
│   └── main.py           # FastAPI graph analytics API
├── shared/               # Shared configs & schemas
├── deployment/           # Dockerfiles & Nginx configs
├── tests/                # Unit and integration test suites
└── research/             # IEEE Paper draft, benchmarks
```

---

## 2. Naming Conventions & Coding Standards

1. **Python (Engines):**
   - Follow **PEP 8** guidelines.
   - Use snake_case for functions and variables: `heal_topology()`, `max_gap_meters`.
   - Use PascalCase for classes: `StressTestEngine`.
   - Use capitalized safe unicode strings in prints (`[OK]` instead of emojis to avoid Windows console errors).
2. **TypeScript (Frontend & Backend):**
   - Follow standard **ESLint/TSLint** guidelines.
   - Use camelCase for variables and functions: `connectDB()`, `sourceNode`.
   - Use PascalCase for React components and models: `MapComponent`, `City`.
   - Use Interface definitions for all API request/response structures.

---

## 3. Testing Architecture

- **Python Tests:** Executed using `pytest`. Located in `/tests` directory:
  - `tests/unit/test_skeletonization.py`: Thinning validation.
  - `tests/unit/test_healing.py`: Angular-alignment MST gap connection tests.
  - `tests/unit/test_stress_test.py`: Target ablate resilience index checks.
- **Express Backend Tests:** Executed using Jest and supertest:
  ```bash
  npm --prefix backend run test
  ```
- **Next.js Frontend Tests:** Build validation tests to ensure code compiles before commits:
  ```bash
  npm --prefix frontend run build
  ```
