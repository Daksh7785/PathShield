# Release Notes — RouteGuard AI v1.1.0

We are proud to announce the **v1.1.0** release of **RouteGuard AI**, transition from a static city workbench into a globally deployable, multi-language, and service-oriented Distributed AI-Native Geospatial Platform.

---

## What's New in v1.1.0

### 1. Global Multi-Language (i18n) & RTL Layouts
- **11-Language Expansion**: Core interfaces now support English (`en`), Spanish (`es`), French (`fr`), German (`de`), Portuguese (`pt`), Arabic (`ar`), Chinese (`zh`), Japanese (`ja`), Hindi (`hi`), Russian (`ru`), and Korean (`ko`).
- **Dynamic Direction Shifting (LTR/RTL)**: Layout containers automatically shift direction attribute `dir={lang === 'ar' ? 'rtl' : 'ltr'}` when Arabic is chosen.
- **Client Session i18n Synchronization**: Preferred locale settings are persisted in `localStorage` across page routing transitions (Overview, GIS Map, Simulations, Rankings, Marketplace).

### 2. Distributed API Gateway & Caching Layer
- **API Gateway**: Embedded request logger middleware, bearer JWT verification, dynamic API key validations, and request rate-limiting.
- **Caching Layer**: Local memory caching middleware with Redis design to accelerate metadata query reads.

### 3. Model Registry & Drift Monitoring
- **Orchestration**: GPU/CPU scheduling optimizer, fallback model fallback routing logic.
- **Model Registry**: Centralized catalog storing SegFormer and Vision Transformer model metadata versions.
- **Drift Detector**: Sliding-window performance monitor evaluating moving-average Intersection over Union (IoU) metrics.

### 4. Graph Analytics & Digital Twin Engines
- **Metrics Expansion**: Implemented NetworkX PageRank, Closeness Centralities, and network fragmentation indicators.
- **Digital Twin Store**: Capture topological snapshots of nodes, edges, active hazards, and congestion layers at explicit timestamps with timeline replay controls.

### 5. Geospatial PostGIS & Vector Data Models
- **PostGIS Schema**: SQL declarations representing multi-tenant organizations, node intersections, road centerline links (`LineString`), and disaster contours (`Polygon`) with spatial `GIST` indexes.
- **Vector DB Client**: Client interfaces matching Qdrant indexing and similarity queries for the AI Copilot.
- **NATS Message Broker**: Publisher-Subscriber client simulating message stream brokers for real-time traffic events.

---

## Verification & Testing

- **Backend (Jest Router)**: 3/3 tests passing.
- **Python Engines (Pytest)**: 19/19 tests passing.
- **TypeScript Types (npx tsc)**: Zero compile errors.
- **Production Build (npm run build)**: Fully compiled and optimized Next.js bundle.
