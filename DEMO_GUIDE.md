# Demo Guide — Route Resilience Urban Mobility Platform

This guide helps presenters and judges run through the Route Resilience platform features.

---

## 1. Five-Minute Presentation Outline

1.  **Introduce the Problem:** Standard satellite imagery suffers from "spectral blindness" due to foliage, building shadows, and clouds. Gaps in road masks make them useless for routing engines.
2.  **The Solution:** An end-to-end pipeline:
    -   *Deep Learning:* A Vision Transformer (ViT-B/32) segmenter that uses self-attention to see under tree cover.
    -   *Topological Healing:* Rebuilds fragmented paths using Minimum Spanning Trees (MST) and Disjoint Sets with vector direction (angular) consistency checks.
    -   *Analysis Engine:* Computes Brandes Betweenness Centrality to locate "Gatekeeper Nodes" and conducts node ablation simulations to map detour impacts.
3.  **Live Walkthrough:**
    -   Open the **City Overview** page at `http://localhost:8501`. Select **Bengaluru** to display the road layout and the bottleneck heatmap.
    -   Navigate to **Stress Test**. Select **Single Node Removal**, pick the top bottleneck node, click **Run Stress Test**, and point out the Resilience Index and detour factor.
    -   Open **Disaster Scenario**. Select **Flood Simulation**, input bounding coordinates, run it, and show the estimated travel time delay and rerouted roads.

---

## 2. Common Judge Questions & Answers

### Q1: Why use a Vision Transformer (ViT) instead of a standard ResNet U-Net?
*   *Answer:* Convolutions in CNNs process images locally (small receptive fields). If tree canopy covers a road for 50 meters, a CNN sees only tree pixels and predicts a gap. Vision Transformers utilize self-attention mechanisms to model global dependencies, allowing the network to connect road segments on both sides of a canopy block based on linear continuity.

### Q2: How does the topological healing ensure we don't draw unrealistic road connections?
*   *Answer:* We don't just connect the nearest endpoints. We compute the directional vector of incoming roads. A candidate connection is evaluated using a combined score:
    $$\text{Score} = w_1 \cdot \text{Distance} + w_2 \cdot \text{AngularDeviation}$$
    If the endpoints do not point towards each other within a $35^\circ$ angular threshold, the connection is rejected.

### Q3: How do you handle metric length calculations in a lat-long coordinate system?
*   *Answer:* All spatial geometries are projected from EPSG:4326 (lat/long) to the local UTM zone (e.g., UTM zone 43N for Bengaluru) during graph construction. This ensures all distance measurements are in metrically precise meters rather than degrees.
