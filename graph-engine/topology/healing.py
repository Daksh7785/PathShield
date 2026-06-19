"""
Topological healing of fragmented road networks.
Bridges gaps using a custom Union-Find and MST Kruskal-based algorithm
with angular vector alignment validation.
"""
import cv2
import numpy as np
import networkx as nx
from scipy.spatial import cKDTree
from typing import List, Tuple, Optional
from skimage.draw import line as draw_line


def compute_local_direction(
    skeleton: np.ndarray,
    point: Tuple[int, int],
    search_radius: int = 10
) -> Optional[float]:
    """
    Estimate the local road direction at a skeleton endpoint.
    Looks at nearby skeleton pixels to determine orientation.
    
    Returns: angle in degrees [0, 180), or None if no neighbors found
    """
    y, x = point
    H, W = skeleton.shape
    
    # Collect nearby skeleton pixels within search radius
    nearby = []
    for dy in range(-search_radius, search_radius + 1):
        for dx in range(-search_radius, search_radius + 1):
            ny, nx_ = y + dy, x + dx
            if (0 <= ny < H and 0 <= nx_ < W and
                    skeleton[ny, nx_] and (dy != 0 or dx != 0)):
                nearby.append((dy, dx))
    
    if not nearby:
        return None
    
    # Weighted average direction
    dys = np.array([n[0] for n in nearby])
    dxs = np.array([n[1] for n in nearby])
    weights = 1.0 / (np.sqrt(dys**2 + dxs**2) + 1e-8)
    
    avg_dy = np.average(dys, weights=weights)
    avg_dx = np.average(dxs, weights=weights)
    
    angle = np.degrees(np.arctan2(avg_dy, avg_dx)) % 180
    return angle


def angular_compatibility(angle1: Optional[float], angle2: Optional[float], threshold: float = 35.0) -> bool:
    """
    Check if two road endpoints are angularly compatible for bridging.
    Two endpoints can be connected if their road directions roughly align
    (i.e., they look like two ends of the same road interrupted by occlusion).
    """
    if angle1 is None or angle2 is None:
        return True  # Can't check, allow connection
    
    diff = abs(angle1 - angle2) % 180
    if diff > 90:
        diff = 180 - diff
    
    return diff <= threshold


class UnionFind:
    """Disjoint Set Union (DSU) implementation for managing component merges."""
    def __init__(self, elements):
        self.parent = {el: el for el in elements}
        self.rank = {el: 0 for el in elements}

    def find(self, i):
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            if self.rank[root_i] < self.rank[root_j]:
                self.parent[root_i] = root_j
            elif self.rank[root_i] > self.rank[root_j]:
                self.parent[root_j] = root_i
            else:
                self.parent[root_j] = root_i
                self.rank[root_i] += 1
            return True
        return False


def get_component_label(pt: Tuple[int, int], cc_label: np.ndarray) -> int:
    """Find the connected component index for a given skeleton coordinate."""
    y, x = pt
    H, W = cc_label.shape
    # Check coordinate directly first
    if cc_label[y, x] > 0:
        return int(cc_label[y, x])
    # Search in a local 3x3 neighborhood if slightly offset
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and cc_label[ny, nx] > 0:
                return int(cc_label[ny, nx])
    return 0


def heal_topology(
    skeleton: np.ndarray,
    endpoints: List[Tuple[int, int]],
    junctions: List[Tuple[int, int]],
    max_gap_px: int = 50,
    angular_threshold: float = 35.0,
) -> np.ndarray:
    """
    Bridge gaps in road skeleton using a hybrid Union-Find + MST healing algorithm.
    
    Algorithm:
    1. Identify connected components of the raw road skeleton.
    2. Extract endpoints and compute local directions.
    3. Generate candidate bridges between endpoints within max_gap_px.
    4. Sort candidate bridges by distance weight.
    5. Apply Kruskal's MST logic via Union-Find: select the shortest, angularly
       compatible bridges that merge disjoint components.
    6. Draw the resolved bridges onto the healed skeleton.
    """
    healed = skeleton.copy()
    
    if len(endpoints) < 2:
        return healed
        
    # Step 1: Find connected components BEFORE healing
    cc_mask = skeleton.astype(bool)
    cc_label, n_components = _label_components(cc_mask)
    
    if n_components <= 1:
        return healed

    # Step 2: Initialize Union-Find over active connected component labels
    component_labels = list(range(1, n_components + 1))
    uf = UnionFind(component_labels)

    # Step 3: Pre-compute local directions for all candidate endpoints
    directions = {}
    for i, pt in enumerate(endpoints):
        directions[i] = compute_local_direction(skeleton, pt)

    # Step 4: Build candidate bridges list
    coords = np.array(endpoints)
    tree = cKDTree(coords)
    pairs = tree.query_pairs(r=max_gap_px)

    candidate_bridges = []
    for i, j in pairs:
        if i == j:
            continue

        # Fetch component labels for the endpoints
        c_i = get_component_label(endpoints[i], cc_label)
        c_j = get_component_label(endpoints[j], cc_label)

        if c_i == 0 or c_j == 0 or c_i == c_j:
            continue  # Ignore endpoints inside same component or unmapped

        # Validate angular alignment
        if not angular_compatibility(directions[i], directions[j], angular_threshold):
            continue

        # Calculate Euclidean distance
        pt1 = np.array(endpoints[i])
        pt2 = np.array(endpoints[j])
        dist = np.linalg.norm(pt1 - pt2)

        candidate_bridges.append({
            "u": i,
            "v": j,
            "c_u": c_i,
            "c_v": c_j,
            "weight": dist
        })

    # Step 5: Sort candidate bridges by distance (Kruskal's order)
    candidate_bridges.sort(key=lambda x: x["weight"])

    # Step 6: Select bridges using Union-Find to form minimum spanning tree of components
    selected_bridges = []
    for bridge in candidate_bridges:
        c_u = bridge["c_u"]
        c_v = bridge["c_v"]

        # If they belong to disjoint components, merge them
        if uf.find(c_u) != uf.find(c_v):
            uf.union(c_u, c_v)
            selected_bridges.append((bridge["u"], bridge["v"]))

    # Step 7: Draw selected bridges onto the healed skeleton
    H, W = skeleton.shape
    bridges_drawn = 0
    
    for u_idx, v_idx in selected_bridges:
        pt1 = endpoints[u_idx]
        pt2 = endpoints[v_idx]
        
        # Draw line using Bresenham's algorithm
        rr, cc = draw_line(pt1[0], pt1[1], pt2[0], pt2[1])
        valid = (rr >= 0) & (rr < H) & (cc >= 0) & (cc < W)
        healed[rr[valid], cc[valid]] = 1
        bridges_drawn += 1

    # Step 8: Calculate metrics for reporting
    n_components_after = _count_components(healed)
    connectivity_score = 1.0 - (n_components_after - 1) / (n_components - 1) if n_components > 1 else 1.0
    topology_quality_score = 1.0 - (bridges_drawn * 0.05) # Penalty for excessive bridging
    topology_quality_score = max(0.1, min(1.0, topology_quality_score))

    print(f"✓ Healing: {bridges_drawn} bridges drawn via Kruskal MST | "
          f"Components: {n_components} → {n_components_after} | "
          f"Connectivity Score: {connectivity_score:.3f} | "
          f"Topology Quality Score: {topology_quality_score:.3f}")
          
    return healed


def _label_components(binary: np.ndarray):
    """Label connected components in binary image."""
    from skimage.measure import label
    labeled = label(binary)
    return labeled, labeled.max()


def _count_components(skeleton: np.ndarray) -> int:
    """Count connected components in skeleton."""
    _, n = _label_components(skeleton.astype(bool))
    return n
