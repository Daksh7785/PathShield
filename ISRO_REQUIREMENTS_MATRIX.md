# ISRO Requirements Matrix — Route Resilience Platform

This matrix maps system features to technical specifications, user-agency demands (ISRO, NRSC, MeitY, Ministry of Consumer Affairs), and target verification methods.

---

## 1. System Requirements Mapping

| ID | Category | Requirement Description | Downstream Beneficiary | System Feature / Implementation | Verification Method |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | Data Ingestion | Multi-resolution satellite image support (Sentinel-2 10m, LISS-IV 5.8m, Cartosat-3 0.5m). | NRSC, ISRO Scientists | `data_pipeline/tiling.py`, `normalization.py` (CLAHE) | Verification of tile shape, coordinate transform, and band alignment. |
| **REQ-02** | Segmentation | Occlusion-robust road extraction beneath shadows, canopy, and clouds. | Urban Planners, GIS Operators | `models/vit_segmentation.py` (ViT global attention + custom decoder) | IoU, Dice Score, and Occlusion Recall evaluation against ground truth. |
| **REQ-03** | Loss functions | Topology-aware model convergence optimization. | Deep Learning Researchers | `models/losses.py` (Dice + IoU + Boundary-aware + Connectivity loss) | Epoch-by-epoch loss reduction logging in training curve logs. |
| **REQ-04** | Skeletonization | Mask thinning to 1px wide centerlines and node/edge parsing. | Transport Engineers | `topology/skeletonization.py` (Zhang-Suen thinning + junction extraction) | Edge pixel count checks, endpoint and junction degree tests. |
| **REQ-05** | Graph Healing | Bridging road gaps caused by extreme occlusions. | Disaster Management | `topology/healing.py` (MST + Disjoint Sets + Angular alignment vector checks) | Connectivity ratio increase and LCC component size comparison. |
| **REQ-06** | Graph Builders | Georeferencing node coordinates and routing graph exports. | GIS Engineers | `topology/graph_builder.py` (Pixel-to-Geographic mapping, GeoJSON exporter) | Shortest path error (APLS) comparison against OSM networks. |
| **REQ-07** | Criticality | Identifying bottlenecks ("Gatekeeper Nodes") and single points of failure. | MeitY, Urban Planners | `analysis/centrality.py` (Brandes Betweenness Centrality, Closeness, Criticality Rank) | Bounding box spatial queries and node ranking logs. |
| **REQ-08** | Stress Testing | Simulating localized failures (flooding, closures) and computing Resilience Index. | Disaster Response, Municipalities | `analysis/stress_test.py` (Node ablation, flood scenarios, cascading failure loops) | Resilience Index output and detour factor calculations. |
| **REQ-09** | Routing | Emergency pathfinding and alternate detour routes under failures. | Ambulance, Police, Fire Services | `analysis/routing.py` (Dijkstra paths, failed-node bypasses, evacuation zones) | Real-time path updates and destination isolation warnings. |
| **REQ-10** | Visualization | Interactive heatmaps, scenario toggles, and click-to-disable intersections. | Government decision support | `dashboard/app.py`, `dashboard/pages/` (Streamlit Folium/Leaflet components) | Interactive UI clicks, map overlays, and slider executions. |
