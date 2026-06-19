"""
Convert healed skeleton to NetworkX graph and export as GeoJSON.
Nodes = junctions + endpoints. Edges = skeleton paths between nodes.
"""
import json
import numpy as np
import networkx as nx
from typing import Tuple, List, Dict, Optional
from collections import deque


def pixel_to_geographic(px: int, py: int, bounds: tuple, width: int, height: int) -> Tuple[float, float]:
    """Convert pixel (x,y) to geographic (longitude, latitude)."""
    minx, miny, maxx, maxy = bounds
    lng = minx + (px / width) * (maxx - minx)
    lat = maxy - (py / height) * (maxy - miny)
    return round(lng, 8), round(lat, 8)


def trace_edge_path(
    skeleton: np.ndarray,
    start: Tuple[int, int],
    end: Tuple[int, int],
    node_set: set,
) -> List[Tuple[int, int]]:
    """
    Trace the skeleton path between two nodes using BFS.
    Returns list of pixel coordinates forming the edge path.
    """
    H, W = skeleton.shape
    start_y, start_x = start
    end_y, end_x = end
    
    visited = set()
    queue = deque([(start_y, start_x, [(start_y, start_x)])])
    
    while queue:
        y, x, path = queue.popleft()
        
        if (y, x) in visited:
            continue
        visited.add((y, x))
        
        if (y, x) == (end_y, end_x):
            return path
        
        # Explore 8-connected neighbors
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue
                ny, nx_ = y + dy, x + dx
                if (0 <= ny < H and 0 <= nx_ < W and
                        skeleton[ny, nx_] and (ny, nx_) not in visited):
                    # Don't pass through other nodes (except destination)
                    if (ny, nx_) in node_set and (ny, nx_) != (end_y, end_x):
                        continue
                    queue.append((ny, nx_, path + [(ny, nx_)]))
    
    return [start, end]  # Direct line if no path found


def skeleton_to_graph(
    skeleton: np.ndarray,
    nodes: dict,
    bounds: tuple,
    city_id: str = "unknown",
) -> nx.Graph:
    """
    Convert healed skeleton + extracted nodes to a geographic NetworkX graph.
    
    Args:
        skeleton: (H, W) binary healed skeleton
        nodes: {'junctions': [...], 'endpoints': [...]}
        bounds: (minx, miny, maxx, maxy) in WGS84
        city_id: City identifier for node attributes
    
    Returns:
        NetworkX Graph with geographic node attributes
    """
    H, W = skeleton.shape
    G = nx.Graph()
    
    # Combine all node types
    all_nodes = (
        [(y, x, 'junction') for y, x in nodes.get('junctions', [])] +
        [(y, x, 'endpoint') for y, x in nodes.get('endpoints', [])]
    )
    
    if not all_nodes:
        print("⚠ No nodes found in skeleton")
        return G
    
    # Add nodes to graph
    node_set = set()
    node_idx_map = {}
    
    for idx, (y, x, ntype) in enumerate(all_nodes):
        lng, lat = pixel_to_geographic(x, y, bounds, W, H)
        degree = sum(1 for dy in [-1,0,1] for dx in [-1,0,1]
                     if not (dy==0 and dx==0) and 0<=y+dy<H and 0<=x+dx<W and skeleton[y+dy,x+dx])
        
        G.add_node(idx,
                   pos=(lng, lat),
                   pixel_pos=(x, y),
                   longitude=lng,
                   latitude=lat,
                   node_type=ntype,
                   degree=degree,
                   city_id=city_id,
                   betweenness_centrality=0.0,
                   criticality_score=0.0,
                   is_gateway=(degree == 1))
        
        node_set.add((y, x))
        node_idx_map[(y, x)] = idx
    
    # Trace edges between adjacent nodes via skeleton paths
    node_array = [(y, x) for y, x, _ in all_nodes]
    edges_added = set()
    
    from scipy.spatial import cKDTree
    coords = np.array(node_array)
    tree = cKDTree(coords)
    
    for idx, (y, x, _) in enumerate(all_nodes):
        # Find nearest nodes within search radius
        nearby_idxs = tree.query_ball_point([y, x], r=100)
        
        for j_idx in nearby_idxs:
            if j_idx <= idx:
                continue
            
            jy, jx = node_array[j_idx]
            edge_key = tuple(sorted([idx, j_idx]))
            
            if edge_key in edges_added:
                continue
            
            # Check if they're connected via skeleton
            path = trace_edge_path(skeleton, (y, x), (jy, jx), node_set)
            
            if len(path) > 1:
                # Calculate edge length in meters (approximate)
                path_arr = np.array(path)
                pixel_dists = np.sqrt(np.diff(path_arr[:, 0])**2 + np.diff(path_arr[:, 1])**2)
                total_pixels = pixel_dists.sum()
                
                # Approximate: 1 pixel ≈ resolution_m meters (configurable)
                length_m = total_pixels * 1.0  # Will be calibrated per city
                
                path_coords = [
                    pixel_to_geographic(px_, py_, bounds, W, H)
                    for py_, px_ in path[::5]  # Sample every 5th point
                ]
                
                G.add_edge(idx, j_idx,
                           weight=length_m,
                           length_meters=round(length_m, 2),
                           pixel_path_length=len(path),
                           geometry=path_coords,
                           confidence=1.0,
                           is_healing_edge=False)
                
                edges_added.add(edge_key)
    
    print(f"✓ Graph: {G.number_of_nodes()} nodes | {G.number_of_edges()} edges")
    return G


def graph_to_geojson(G: nx.Graph, output_path: Optional[str] = None) -> dict:
    """Export NetworkX graph to GeoJSON FeatureCollection."""
    features = []
    
    # Nodes as Point features
    for node_id, attrs in G.nodes(data=True):
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(attrs.get("longitude", 0)), float(attrs.get("latitude", 0))]
            },
            "properties": {
                "id": int(node_id),
                "node_type": attrs.get("node_type", "unknown"),
                "degree": int(attrs.get("degree", 0)),
                "betweenness_centrality": float(attrs.get("betweenness_centrality", 0)),
                "criticality_score": float(attrs.get("criticality_score", 0)),
                "is_gateway": bool(attrs.get("is_gateway", False)),
                "city_id": attrs.get("city_id", ""),
            }
        }
        features.append(feature)
    
    # Edges as LineString features
    for u, v, attrs in G.edges(data=True):
        u_pos = G.nodes[u].get("pos", (0, 0))
        v_pos = G.nodes[v].get("pos", (0, 0))
        
        geometry = attrs.get("geometry", [u_pos, v_pos])
        if not geometry:
            geometry = [u_pos, v_pos]
        
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[float(coord[0]), float(coord[1])] for coord in geometry]
            },
            "properties": {
                "source": int(u),
                "target": int(v),
                "length_meters": float(attrs.get("length_meters", 0)),
                "confidence": float(attrs.get("confidence", 1.0)),
                "is_healing_edge": bool(attrs.get("is_healing_edge", False)),
            }
        }
        features.append(feature)
    
    geojson = {"type": "FeatureCollection", "features": features}
    
    if output_path:
        with open(output_path, "w") as f:
            json.dump(geojson, f, indent=2)
        print(f"✓ GeoJSON exported → {output_path}")
    
    return geojson
