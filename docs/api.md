# RouteGuard AI — API Specification

This document details the HTTP endpoints exposed by the API Gateway and the Python microservices.

## API Gateway (`http://localhost:8000`)

### 1. Cities Controller
- **`GET /api/v1/cities`**
  - Returns a list of all configured global cities (Bengaluru, Delhi, Mumbai, New York, Tokyo) with high-level statistics.
- **`GET /api/v1/cities/:cityId`**
  - Returns detailed node-link graph data (JSON format) for a specific city.

### 2. Simulation & Routing Controller
- **`POST /api/v1/simulations/:cityId/route`**
  - Calculates the shortest path and alternative detour routes between a source and target node.
  - Automatically factors in active road closure incidents and scales weights based on current traffic.
- **`POST /api/v1/simulations/:cityId/stress-test`**
  - Triggers a stress-test simulation (Flood bounds, ablation list, or cascading seed).
  - Returns resilience indexes and mitigation recommendations.
- **`GET /api/v1/simulations/feed/disasters`**
  - Exposes live mock warning coordinates from NASA FIRMS and GDACS alerts.
- **`POST /api/v1/simulations/feed/copilot`**
  - Handles natural-language chatbot requests from the client.

### 3. Traffic Controller
- **`GET /api/v1/traffic/:cityId/congestion`**
  - Retrieves active road-segment congestion multipliers and localized construction incidents.

---

## Python Graph Engine (`http://localhost:8003`)

- **`POST /skeletonize`**: Translates a base64 road mask into skeleton coordinates.
- **`POST /heal`**: Connects fragmented skeletons using distance and angle heuristics.
- **`POST /centrality`**: Calculates betweenness and closeness centrality scores.
- **`POST /route`**: Dynamic traffic-aware routing engine.
- **`POST /stress-test`**: Node/edge failure simulation engine.
