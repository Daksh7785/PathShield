# RouteGuard AI — Tech Stack Decisions
## Architectural Rationale for Systems Ingestion and Analytics

This document explains the technical rationale behind the selection of the RouteGuard AI technology stack.

---

## 1. Frontend: Next.js, React, TypeScript, Tailwind, & Leaflet

- **Next.js & React:** Next.js provides static site generation (SSG) and server-side rendering (SSR), enabling instant loading of dashboard components. Using React allows a modular, component-based layout for toggling GIS layers and simulation controls.
- **TypeScript:** Enforces strict type safety across geo-coordinates, node objects, and routing request schemas, reducing runtime errors.
- **Leaflet & MapLibre:** High-performance, lightweight GIS rendering engines. Leaflet handles the overlay of hundreds of nodes, standard road polylines, healed dashed edges, and shortest path corridors smoothly in the client browser.
- **Tailwind CSS & ShadCN:** Tailwind provides maximum styling flexibility, allowing a premium dark-mode glassmorphic interface that improves scannability.

---

## 2. Backend: Node.js, Express.js, & TypeScript

- **Express.js:** Exposes a fast, clean HTTP gateway server. Express acts as the primary orchestrator, directing client dashboard requests to MongoDB, Redis, or delegating heavy spatial/deep learning calculations to the Python microservices.
- **Socket.IO:** Enables real-time, bi-directional event streaming. When a user triggers a cascading failure simulation, progress logs and affected node sequences are pushed instantly to the frontend.
- **Rate Limiting & CORS:** Secures the gateway against denial-of-service attempts.

---

## 3. Databases: MongoDB, PostGIS, & Redis Cache

- **MongoDB (Mongoose):** Storing urban networks (cities, nodes, edges) as document structures is highly efficient. Mongoose schemas model the graph data natively, with an in-memory database fallback to guarantee 100% local offline execution.
- **PostgreSQL & PostGIS:** Provides spatial indexing and query support (e.g. bounding box polygon intersection queries for flood simulations) using standard spatial structures:
  ```sql
  SELECT id FROM nodes WHERE ST_Contains(ST_GeomFromText('POLYGON(...)'), geom);
  ```
- **Redis Cache:** Caches Brandes centrality scores and Dijkstra path calculations. If a user requests a path between the same origin-destination pair multiple times, Redis serves it instantly.

---

## 4. Machine Learning & Graph Engines: PyTorch & NetworkX

- **PyTorch:** The primary library for deep learning. PyTorch's autograd engine and Vision Transformer support (via `timm`) enable training and fast sliding-window inference on road tiles.
- **NetworkX:** A mature, highly optimized Python package for network analysis. NetworkX implements Brandes Betweenness Centrality, Dijkstra's shortest path, and minimum spanning trees.
