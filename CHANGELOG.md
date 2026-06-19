# Changelog

All notable changes to the **RouteGuard AI** platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-20

### Added
- **Global Data Geocoding Search**: Integrated Nominatim OpenStreetMap API geocoder inside Next.js GIS page to re-center the map on searched cities or coordinate epicenters.
- **AI Mobility Copilot**: Implemented a floating glassmorphic chatbot component (`CopilotChat.tsx`) in the GIS dashboard communicating with backend routes for answering natural-language mobility resilience queries.
- **Traffic Engine & Incidents**: Added `backend/src/routes/traffic.ts` to simulate traffic congestion levels (heavy, moderate, clear) and road construction or closure incidents.
- **Disaster Overlay Layers**: Integrated NASA FIRMS active fire hotspots and GDACS flood warning circles directly into Leaflet `MapComponent.tsx` as map overlays with hover popups.
- **Traffic-Aware Routing**: Updated Python Graph Engine `shortest_path` and `k_shortest_paths` to consume dynamic edge weights scaled by traffic friction multipliers and remove disabled/closed edges.
- **Jest Router Test Suite**: Added a comprehensive router unit test suite (`backend/src/__tests__/routes.test.ts`) that mocks Express requests and tests simulations, disasters, and traffic endpoints.

### Changed
- **Multi-City Mock DB**: Rewrote database seeder (`backend/src/config/db.ts`) to automatically populate Delhi, Mumbai, New York, Tokyo, and Bengaluru networks on fallback.
- **Next.js Page Layout**: Updated the main GIS workbench to incorporate Nominatim search, disaster alerts list, traffic incidents panel, and Copilot widget.

### Fixed
- **Pytest collection mismatch**: Restricted pytest target to `tests/` directory to prevent import conflicts with duplicated class names.
- **Model Import References**: Fixed VisionTransformer import errors in Python AI engine startup scripts.
