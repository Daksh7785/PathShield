# RouteGuard AI — Emergency Engine
## Critical Dispatch Routing and Evacuation Coordination

This document details the route planning and reachability algorithms used to coordinate rescue efforts during urban emergencies.

---

## 1. Emergency Facility Reachability Analysis

During natural disasters (e.g. urban flooding), dispatching emergency vehicles (ambulances, fire engines) requires finding paths that avoid flooded streets.

- **Source:** Emergency station coordinates (fire station, hospital).
- **Target:** Affected residential sectors.
- **Routing Constraint:** Standard Dijkstra pathfinding is modified to exclude all deactivated edges and nodes:
  $$\text{Path} = \text{DijkstraShortestPath}(G \setminus \mathcal{V}_f, \text{source}, \text{target})$$
- **Detour Overhead:** Calculates the increase in ambulance response time based on detour lengths and a standard speed modifier ($40\text{ km/h}$).

---

## 2. Evacuation Corridor Planning

To evacuate a flooded suburb to safety shelters:
1. **Origin Sector Definition:** Defines a bounding box around the affected residential area.
2. **Safe Destinations:** A list of active, safe shelter node IDs outside the disaster zone.
3. **Corridor Synthesis:** Computes shortest paths from all origin nodes to their nearest safe destination:
   $$\text{Corridors} = \{ \text{shortest\_path}(G \setminus \mathcal{V}_f, o, d_{\text{nearest}}) \mid o \in \text{Origins} \}$$
4. **Capacity Planning:** Intersects corridors to identify overlapping road segments, highlighting potential evacuation bottlenecks where traffic congestion will occur.

---

## 3. Alternative Backup Routes (Evacuation Risks)

If a primary evacuation corridor fails, the engine computes $k$-alternative paths using Yen's algorithm:
- **Primary Corridor:** Shortest path.
- **Backup Corridor:** Next shortest path that does not share more than 20% of its edges with the primary corridor.
- **Result:** Provides a fallback evacuation map displayed on the Next.js dashboard.
