# RouteGuard AI — Innovation Report
## Beyond-the-Baseline Features for Route Resilience

This report details the advanced, high-value features built into the RouteGuard AI platform that extend beyond the baseline requirements of the hackathon problem statement.

---

## 1. Dynamic Routing & Traffic Friction Models

### Travel Time Weighted Edges
- *Standard Approach:* Graph edges are weighted purely by Euclidean distance (meters).
- *RouteGuard AI:* We assign a dynamic travel time weight based on road type, confidence score, and simulated traffic friction:
  $$\text{Weight} = \frac{\text{Length (meters)}}{\text{Speed limit (m/s)}} \times f_{\text{friction}}$$
  Where $f_{\text{friction}}$ is derived from road narrowing (detected via mask width) and the edge's occlusion level. If an edge has a high occlusion level, its confidence is lower, slightly increasing its transit cost to prioritize open, validated roads for emergency routing.

---

## 2. Disaster Response & Isolation Risk Analysis

### Emergency Service Isolation Risk Index (ES-IRI)
We identify isolated subgraphs (connected components that no longer connect to nodes designated as "Critical Facilities"). We compute the percentage of the city's area and population that falls into these "critical isolation zones."

### Interactive Polygon-Based Flood Simulation
The dashboard allows users to draw a custom polygon on the map or select a simulated reservoir breach. The backend translates this polygon into a spatial query. All intersecting nodes are disabled in a single batch, and the system instantly recalculates rerouting paths and outputs a dynamic travel time delay index.

---

## 3. Structural Graph Innovations

### Route Redundancy Score (RRS)
For every pair of source-target zones, we calculate the number of node-disjoint shortest paths. A high Route Redundancy Score indicates that even if primary paths fail, alternative, non-overlapping routes exist. Neighborhoods with an RRS of 1 are flagged as high-risk bottlenecks.

### Cascading Failure & Traffic Redistribution
When a high-betweenness node is ablated, we redistribute its shortest-path traffic loads onto alternative routes. If the load on an alternative edge exceeds its calculated capacity limit (based on road width), we trigger a cascading failure (slowing speeds by 80% or disabling the edge entirely), simulating urban collapse.

---

## 4. Explainable AI (XAI) & Confidence Layers

- **Confidence Score Maps:** Generates a confidence probability layer ($[0.0, 1.0]$) for every extracted road pixel and healed edge, displaying high, medium, and low reliability layers.
- **Attention Map Visualization:** Exposes internal self-attention maps of the Vision Transformer, visually explaining why the model infers road presence beneath thick canopy covers and shadows.
