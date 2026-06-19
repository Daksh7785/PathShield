"""
Topological healing of fragmented road skeletons.
Bridges gaps using Minimum Spanning Tree with angular alignment validation.
This is the key innovation — prevents false connections while recovering
true roads hidden under occlusions.
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


def heal_topology(
    skeleton: np.ndarray,
    endpoints: List[Tuple[int, int]],
    junctions: List[Tuple[int, int]],
    max_gap_px: int = 50,
    angular_threshold: float = 35.0,
) -> np.ndarray:
    """
    Bridge gaps in skeleton using MST-based healing.
    
    Algorithm:
    1. Find all candidate endpoint pairs within max_gap_px distance
    2. For each pair, check angular compatibility
    3. Build a graph of valid candidate bridges weighted by distance
    4. Use minimum spanning tree to select optimal bridges
    5. Draw bridges onto skeleton
    
    Args:
        skeleton: (H, W) binary skeleton
        endpoints: List of (y, x) endpoint coordinates
        junctions: List of (y, x) junction coordinates
        max_gap_px: Maximum pixel distance to consider bridging
        angular_threshold: Maximum angle difference (degrees) for valid bridge
    
    Returns:
        Healed skeleton with bridges drawn
    """
    healed = skeleton.copy()
    
    if len(endpoints) < 2:
        return healed
    
    # All connectable points = endpoints + far-from-junction endpoints
    candidates = list(endpoints)  # Endpoints are primary candidates
    
    if not candidates:
        return healed
    
    # Build KD-tree for fast nearest-neighbor search
    coords = np.array(candidates)
    tree = cKDTree(coords)
    
    # Find all pairs within max_gap_px
    pairs = tree.query_pairs(r=max_gap_px)
    
    # Pre-compute local directions for all candidates
    directions = {}
    for i, pt in enumerate(candidates):
        directions[i] = compute_local_direction(skeleton, pt)
    
    # Build candidate bridge graph
    bridge_graph = nx.Graph()
    for i in range(len(candidates)):
        bridge_graph.add_node(i, pos=candidates[i])
    
    for i, j in pairs:
        if i == j:
            continue
        
        # Angular compatibility check
        if not angular_compatibility(directions[i], directions[j], angular_threshold):
            continue
        
        # Distance weight
        pt1 = np.array(candidates[i])
        pt2 = np.array(candidates[j])
        dist = np.linalg.norm(pt1 - pt2)
        
        bridge_graph.add_edge(i, j, weight=dist)
    
    # Find connected components BEFORE healing
    cc_mask = skeleton.astype(bool)
    cc_label, n_components = _label_components(cc_mask)
    
    # For each pair of components, add the lowest-weight bridge
    if n_components <= 1 or not bridge_graph.edges():
        return healed
    
    # Use MST to find optimal bridging (minimum total bridge length)
    try:
        mst = nx.minimum_spanning_tree(bridge_graph, weight='weight')
        selected_bridges = list(mst.edges())
    except Exception:
        selected_bridges = list(bridge_graph.edges())[:20]  # Fallback
    
    # Draw bridges onto skeleton
    H, W = skeleton.shape
    bridges_drawn = 0
    
    for i, j in selected_bridges:
        pt1 = candidates[i]
        pt2 = candidates[j]
        
        # Draw line using Bresenham's algorithm
        rr, cc = draw_line(pt1[0], pt1[1], pt2[0], pt2[1])
        valid = (rr >= 0) & (rr < H) & (cc >= 0) & (cc < W)
        healed[rr[valid], cc[valid]] = 1
        bridges_drawn += 1
    
    print(f"✓ Healing: {bridges_drawn} bridges drawn | {n_components} → {_count_components(healed)} components")
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
