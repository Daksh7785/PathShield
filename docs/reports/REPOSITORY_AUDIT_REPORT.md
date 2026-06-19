# Repository Audit Report

This report classifies the file structure of the RouteGuard AI workspace to ensure a clean, production-grade presentation.

## File Classifications

### 1. Core Production Services
- `backend/src/` — API Gateway controllers, routers, models, and config.
- `frontend/src/` — User Interface pages, maps, graphs, and Copilot.
- `graph-engine/` — Python microservice for NetworkX calculations, routing, and stress testing.
- `ai-engine/` — Python microservice for road segmentation models.
- `gis-engine/` — Python microservice for GDAL/Rasterio geospatial tiling.

### 2. Infrastructure & Deployment Files
- `docker-compose.yml` — Container Orchestration for local and cloud deployment.
- `Dockerfile.backend` / `Dockerfile.dashboard` — Gateway and dashboard containers.
- `backend/Dockerfile` / `frontend/Dockerfile` — Subservice build configurations.
- `graph-engine/Dockerfile` / `ai-engine/Dockerfile` / `gis-engine/Dockerfile` — Engine build configurations.
- `deployment/nginx.conf` — Reverse proxy router.

### 3. Core Configuration Files
- `backend/tsconfig.json` / `backend/jest.config.js` — Typescript and Jest settings.
- `frontend/tsconfig.json` / `frontend/tailwind.config.js` — Next.js and styling settings.
- `.gitignore` — Version control ignore lists.
- `requirements.txt` — Python virtual environment dependencies.

### 4. Production Documentation Files (Retained in `/docs`)
- `docs/architecture.md` — Decoupled system diagrams and data flow.
- `docs/api.md` — HTTP spec for the gateway and FastAPI endpoints.
- `docs/developer_guide.md` — Developer environment setup and testing instructions.
- `docs/user_guide.md` — Platform operation manual.
- `docs/research_paper.md` — Academic methodology and patent proposals.

### 5. Obsolete & Redundant Planning Files (Proposed for Cleanup)
- Root-level markdown planning and research files generated during initial phases.
