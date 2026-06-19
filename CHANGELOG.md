# Changelog

All notable changes to the RouteGuard AI platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] — 2026-06-20

### Added
- **i18n & RTL Layouts**:
  - Expanded utility dictionaries to translate all dashboard modules into 11 languages (English, Spanish, French, German, Portuguese, Arabic, Chinese, Japanese, Hindi, Russian, Korean).
  - Configured layout container direction attribute shifting (`dir="rtl"`) on Arabic selection.
  - Implemented `localStorage` state persistence to preserve language choice across client-side router navigation.
- **Distributed AI-Native Gateway**:
  - Created Express API Gateway containing API Key validations, bearer JWT checks, caching, and rate limiting.
  - Developed AI models registry, GPU task routing scheduling simulator, and moving-average model drift detection.
  - Implemented real-time Event Broker pub-sub wrapper and feature store central structures.
  - Added Digital Twin historical snapshot logging and simulation state replay.
  - Added PostGIS relational database layouts and Qdrant vector client interface.

### Changed
- Refactored `server.ts` to load the versioned API Gateway routes and capture request logs.
- Modified graph main Rest endpoints to compute PageRank, Closeness, and network fragmentation indicators.
- Configured `.gitignore` to ignore Next.js compile metadata (`*.tsbuildinfo`).

---

## [1.0.0] — 2026-06-19

### Added
- **Core GIS & Topology**:
  - Leaflet-backed interactive GIS Map Workbench supporting custom node/edge topological selections.
  - SegFormer road mask predictions and angular continuity vector skeletonization.
  - Live GDACS RSS floods ingestion and NASA FIRMS fire markers.
  - Floating AI Copilot conversational widget for disaster impact queries.

### Changed
- Cleaned up duplicate root-level folders.
- Optimized and simplified `README.md` to reflect production-grade mobility intelligence specifications.
