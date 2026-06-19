# RouteGuard AI — Winning Strategy Report
## Strategic Roadmap for ISRO NNRMS Evaluation

This report presents a competitive analysis contrasting standard hackathon projects with RouteGuard AI's research-grade urban mobility solution.

---

## 1. Competitive Tiers: Standard vs. Winning Approaches

| Feature Area | Average Teams | Top Teams | RouteGuard AI (Winning Strategy) |
| :--- | :--- | :--- | :--- |
| **Segmentation Model** | Standard U-Net with BCE loss | DeepLabV3+ with Dice loss | **ViT-B/32 & SegFormer Encoder** with hybrid Dice + Boundary + Connectivity topological loss. |
| **Occlusion Handling** | Ignore occlusions, leaving broken gaps | Simple post-processing erosion/dilation | **Spatial/Channel Attention Fusion** & **Angular-continuity MST Healing** bridging occluded streets. |
| **Graph Construction** | Pixel coordinate list | NetworkX graph from basic nodes | **Geospatial Projections (UTM)** with accurate metric distances and detailed junction/dead-end classifications. |
| **Resilience Analysis** | Static charts | Precomputed route failures | **Real-Time Stress Testing Engine** executing node ablation, flood boundary queries, and cascading failures. |
| **Dashboard UI** | Simple Python Streamlit app | Basic React frontend | **Next.js & Express Microservice Architecture** with dynamic socket.io updates and MapLibre/Leaflet GIS rendering. |

---

## 2. Overused Ideas vs. Unique Differentiators

### Overused Ideas (Avoid relying solely on these)
- **Basic Pixel-Wise Binary Classification:** Simple binary segmentation is not useful because minor pixel gaps break routing.
- **Euclidean-Only Healing:** Connecting the closest endpoints creates erroneous connections (e.g. bridging parallel streets separated by buildings).
- **Static Evacuation Routes:** Precomputed routes fail during dynamic disasters where roadways collapse.

### Unique Differentiators of RouteGuard AI
1. **Topological Healing Engine:** Evaluates vector direction of road endpoints before bridging. Gaps are bridged only if their angles align ($\theta \le 35^\circ$), preserving road continuity.
2. **Cascading Failure Simulation:** Identifies gatekeeper intersections by ablating a seed node and iteratively removing adjacent nodes based on updated network centralities.
3. **Robust Microservice Communication:** Express.js gateway handles rate-limiting and DB caching, while FastAPI python microservices perform deep learning predictions and graph analytics.
4. **Resilient Local DB Mocks:** If MongoDB or PostgreSQL databases are refused connection locally, the system activates in-memory fallbacks so the dashboard is fully testable and responsive in any offline evaluation booth.
