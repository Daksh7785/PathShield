# Competitive Advantage Report — Winning Strategy for Route Resilience

To secure a winning position in the ISRO Geospatial Hackathon, our implementation must bypass common baseline approaches and target high-fidelity topological reconstruction and interactive decision support.

---

## 1. Feature & Strategy Matrix

| Dimension | Average Teams | Top 10 Teams | Winning Teams (Our Implementation) |
| :--- | :--- | :--- | :--- |
| **Model Backbone** | Standard U-Net (scratch/ResNet) | U-Net++ or DeepLabV3+ (pretrained) | **Vision Transformer (ViT-B/32) Encoder** with a Multi-Scale Decoder using skip connections. |
| **Occlusion Handling** | Standard data augmentations (flips, rotates) | Custom synthetic shadow/canopy additions | **Adaptive CLAHE Preprocessing** + **Context-aware self-attention** to infer roads through occlusions. |
| **Loss Functions** | Binary Cross-Entropy (BCE) | Combined BCE + Dice Loss | **Composite Loss:** Dice (0.4) + IoU (0.3) + Boundary-Aware Sobel (0.2) + Connectivity Penalty (0.1). |
| **Skeletonization** | Naive Zhang-Suen thinning | Zhang-Suen + basic spur pruning | **Zhang-Suen thinning** combined with **confidence filtering** using an auxiliary Edge Head. |
| **Graph Healing** | Nearest-neighbor line drawing | MST gap healing with Euclidean distance | **MST + Disjoint Sets** using a joint scoring function of **Euclidean distance and angular alignment**. |
| **Network Analysis** | Static betweenness centrality | Regional/subgraph centrality maps | **Brandes Betweenness Centrality** with spatial clustering in PostGIS, caching network subgraphs. |
| **Stress Testing** | Random node removal script | Manual single node deletion CLI | **Node Ablation Simulator** modeling cascading failures, flooding, and calculating a global **Resilience Index**. |
| **UI Dashboard** | Static matplotlib charts | Folium map with pre-calculated overlays | **Interactive Streamlit Dashboard** with real-time leaflet rendering, click-to-disable nodes, and live rerouting. |

---

## 2. Technical Differentiation Points

### A. Deep Learning: Seeing Through Trees
*   *The Limitation:* Standard CNNs lose spatial resolution and struggle to maintain context over large occlusions (e.g., a 100m canopy block).
*   *Our Advantage:* By using a **Vision Transformer (ViT-B/32)**, the network utilizes self-attention to correlate road paths across distant parts of the tile. If a road disappears under trees but reappears 80 pixels later on the same linear trajectory, the ViT's self-attention weights bridge this semantic gap, outputting a continuous mask.
*   *The Loss Advantage:* Our **Composite Loss** penalizes broken road structures. The boundary-aware loss sharpens road edges, while the connectivity loss penalizes isolated road pixels, forcing the network to predict continuous linear features.

### B. Topological Reconstruction: Angular-Aware Healing
*   *The Limitation:* Standard healing algorithms draw straight lines to the nearest endpoint. This produces invalid right angles, cross-block shortcuts, and geometrically impossible roads.
*   *Our Advantage:* Our healing engine calculates the direction vector of road segments leading to endpoints. The score for a candidate healing edge is:
    $$\text{Score} = w_1 \cdot \text{Distance} + w_2 \cdot \text{AngularDeviation}$$
    A gap is bridged only if the two endpoints point towards each other within a reasonable angular threshold, ensuring roads follow natural curved trajectories.

### C. Scalable Spatial Database Architecture
*   *The Limitation:* Python-only graphs struggle to scale when modeling an entire city like Bengaluru (millions of edges). Memory issues and long pathfinding latencies make real-time visualization impossible.
*   *Our Advantage:* Using **PostgreSQL with PostGIS**, we offload spatial indexing (GiST), bounds queries, and regional cropping to database-optimized C/C++ routines. Subgraphs are indexed, and API queries are cached via **Redis**, reducing routing query response times to milliseconds.

### D. Urban Resilience Intelligence
*   *The Limitation:* Traditional stress tests just remove random nodes.
*   *Our Advantage:* We implement a dedicated **Stress Testing Engine** simulating realistic disaster scenarios (e.g., raising water levels and disabling all nodes within a PostGIS flood polygon). The Resilience Index dynamically computes how the city's average shortest path increases, providing urban planners with actionable evacuation layouts.
