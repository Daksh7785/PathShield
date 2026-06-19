# RouteGuard AI — Problem Decomposition
## PS-4: Route Resilience: Occlusion-Robust Road Extraction & Graph-Theoretic Criticality Analysis for Urban Mobility

This document presents a comprehensive, scientific decomposition of ISRO Hackathon Problem Statement 4, analyzing the requirements, constraints, and engineering challenges of implementing RouteGuard AI.

---

## 1. Project Context & Objectives

Modern urban centres, particularly rapidly expanding Indian metropolises (e.g., Bengaluru), face a dual challenge in spatial modelling: fragmentation and stagnation. This challenge sits squarely within the mandate of ISRO's National Natural Resources Management System (NNRMS), which seeks to maximise the downstream utility of indigenous remote sensing Earth Observation (EO) satellites such as Cartosat-3 and Resourcesat LISS-4.

Standard satellite-based road extraction often fails due to "spectral blindness" caused by tree canopies, building shadows, and cloud cover. These "broken" masks are useless for real-world applications like disaster response or traffic simulation because they lack topological connectivity. RouteGuard AI solves this by introducing a dual-stage pipeline combining deep learning semantic segmentation with topological graph-theoretic healing.

### Core Objectives
1. **Occlusion-Robust Road Segmentation:** Deep learning model to identify roads under heavy occlusions (vegetation canopies, building shadows, cloud cover, urban clutter).
2. **Topological Skeletonization:** Convert binary segmentation masks to single-pixel wide centerline graphs representing road networks.
3. **Graph Healing Engine:** Bridge topological gaps mathematically using union-find, disjoint sets, and angular MST heuristics to recover road connectivity.
4. **Criticality & Centrality Analysis:** Calculate centrality metrics (Betweenness, Closeness, PageRank) to identify gatekeeper nodes and critical bottlenecks.
5. **Disaster Simulation & Resilience Assessment:** Systematically simulate infrastructure failures (floods, accidents, bridge collapses) to evaluate network efficiency drop.
6. **Decision Support Dashboard:** An interactive Next.js web application displaying geospatial overlays, simulations, and routing detours.

---

## 2. Requirement Matrix & Constraints

| Dimension | Rationale / Target | Implementation Details |
| :--- | :--- | :--- |
| **Spectral Source Inputs** | Multitemporal & multispectral compatibility | Support for Cartosat-3 (0.28m PAN/1.12m MS), LISS-IV (5.8m), Sentinel-2 (10m), SpaceNet, and DeepGlobe. |
| **Explicit Requirements** | Pixel-level classification + topological healing | Semantic segmentation map → Zhang-Suen thinning skeleton → Disjoint Component Healing → Routable Graph. |
| **Evaluation Metrics** | Quantifiable correctness criteria | Segmentation: IoU, Dice, Precision, Recall, Boundary F-score.<br>Graph: Connectivity Ratio, Shortest Path Length ratio, Average Path Length discrepancy. |
| **Technical Constraints** | Windows environment compatibility | Python 3.14 environment dependencies resolved; rasterio/shapely used instead of raw GDAL bindings to prevent local binary compilation blocks. |
| **Hidden Requirements** | Metric/Coordinate transformations | Coordinates must be projected from EPSG:4326 (WGS84) to local metric UTM zones (e.g. EPSG:32643 for South India) to calculate accurate length metrics. |

---

## 3. Existing Weaknesses vs. RouteGuard AI Strategy

1. **Spectral Blindness in Segmentation:** Traditional CNNs classify shadowed pixels strictly based on local color features, leading to gaps. RouteGuard AI uses vision transformers (SegFormer/Mask2Former) to learn long-range context, inferring road presence from global road layouts.
2. **Fragmented Skeletons:** Standard thinning algorithms produce disconnected line segments that fail routing. RouteGuard AI applies an angular-aware Minimum Spanning Tree (MST) healing algorithm that evaluates direction alignment (angle difference $\le 35^\circ$) to connect roads that were visually blocked.
3. **Stale Network Calculations:** Conventional spatial systems precalculate bottlenecks. RouteGuard AI implements dynamic, uvicorn-served NetworkX ablate simulations, recalculating betweenness centralities on-the-fly when nodes are ablated.

---

## 4. Scoring Opportunities for ISRO Evaluation

- **Resilience Index (R):** A mathematically robust metric bounded in $[0.0, 1.0]$ representing how well the network handles disruptions:
  $$R = \left( \frac{\text{LCC}_{\text{perturbed}}}{\text{LCC}_{\text{baseline}}} \right) \cdot \min\left(\frac{L_{\text{baseline}}}{L_{\text{perturbed}}}, 1.0\right)$$
- **Explainable AI (XAI):** Visualizing model attention layers to explain why roads are detected beneath canopy occlusions.
- **Evacuation Rerouting Detours:** Real-time calculation of alternative path lengths and turn overheads during disasters.
