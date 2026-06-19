# RouteGuard AI — Resilience Engine
## Mathematical Modeling of Urban Mobility Network Resilience

This document details the mathematical metrics used by RouteGuard AI to assess and rank the vulnerability of urban road networks.

---

## 1. Network Efficiency and Resilience Index

A network's structural performance is measured using **Global Efficiency** ($E(G)$), which evaluates how easily information or vehicles travel between all node pairs:

$$E(G) = \frac{1}{N(N-1)} \sum_{u \neq v \in G} \frac{1}{d(u,v)}$$

where $d(u,v)$ is the shortest path distance in meters between node $u$ and $v$. If two nodes are disconnected, $d(u,v) = \infty$, so $\frac{1}{d(u,v)} = 0$.

### Resilience Index ($R$)
When a set of nodes or corridors $\mathcal{V}_f$ fails, we measure the impact using the **Resilience Index** ($R$), which scales the efficiency ratio by the fraction of nodes remaining connected in the Largest Connected Component (LCC):

$$R = \left( \frac{\text{LCC}_{\text{perturbed}}}{\text{LCC}_{\text{baseline}}} \right) \cdot \min\left( \frac{E(G \setminus \mathcal{V}_f)}{E(G)}, 1.0 \right)$$

- **$R \approx 1.0$:** High resilience; the network adapts to failures without fragmentation.
- **$R < 0.5$:** Critical vulnerability; the network splits into isolated clusters, disrupting travel.

---

## 2. Accessibility & Evacuation Reachability

### Accessibility Score ($A(u)$)
Measures a neighborhood node's proximity to essential urban hubs (hospitals, fire stations):

$$A(u) = \sum_{h \in \mathcal{H}} \frac{1}{d(u, h)^2}$$

where $\mathcal{H}$ is the set of active healthcare/emergency facilities. A local road blockage nearby dramatically drops $A(u)$ as detours increase.

### Route Redundancy Score (RRS)
Quantifies the number of independent, non-overlapping alternative paths between a suburb (origin) and the city center (destination). RRS is computed using Edge-Disjoint Path counts:

$$\text{RRS}(u, v) = \text{Maximum Number of Edge-Disjoint Paths between } u \text{ and } v$$

---

## 3. Critical Corridor Index (CCI)

Identifies which road segments (edges) act as essential bridges between urban sectors. CCI is computed using edge betweenness centrality:

$$\text{CCI}(e) = \sum_{s \neq t \in G} \frac{\sigma_{st}(e)}{\sigma_{st}}$$

where $\sigma_{st}$ is the total number of shortest paths from node $s$ to $t$, and $\sigma_{st}(e)$ is the number of those paths that pass through edge $e$. High-CCI roads (e.g. city bridges or arterial flyovers) are primary targets for infrastructure reinforcement.
