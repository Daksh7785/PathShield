"""
Routing algorithms (Dijkstra, k-shortest paths, rerouting) for pathfinding
and evacuation simulations under network disruptions.
"""
import networkx as nx
from typing import List, Dict, Optional


def shortest_path(
    G: nx.Graph,
    source: int,
    target: int,
    weight: str = 'weight',
    avoid_nodes: Optional[List[int]] = None
) -> dict:
    """
    Find shortest path between source and target, avoiding failed nodes if specified.
    
    Returns:
        {
          "path": [node_ids],
          "geometry": [[lng, lat], ...],
          "distance_meters": float,
          "turns": int
        }
    """
    if avoid_nodes is None:
        avoid_nodes = []
        
    # Copy graph and remove avoided nodes
    G_temp = G.copy()
    nodes_to_remove = [n for n in avoid_nodes if n in G_temp]
    G_temp.remove_nodes_from(nodes_to_remove)
    
    if source not in G_temp or target not in G_temp:
        return {"error": "Source or target node not accessible due to road closures"}
        
    try:
        path = nx.dijkstra_path(G_temp, source, target, weight=weight)
        dist = nx.dijkstra_path_length(G_temp, source, target, weight=weight)
        
        # Build path coordinates
        geometry = []
        for node_id in path:
            pos = G_temp.nodes[node_id].get("pos", (0, 0))
            geometry.append([float(pos[0]), float(pos[1])])
            
        # Basic turns calculation: check angle changes between edges (simplified)
        turns = 0
        if len(path) > 2:
            for i in range(1, len(path) - 1):
                p1 = G_temp.nodes[path[i-1]].get("pos", (0,0))
                p2 = G_temp.nodes[path[i]].get("pos", (0,0))
                p3 = G_temp.nodes[path[i+1]].get("pos", (0,0))
                
                v1 = (p2[0] - p1[0], p2[1] - p1[1])
                v2 = (p3[0] - p2[0], p3[1] - p2[1])
                
                dot = v1[0]*v2[0] + v1[1]*v2[1]
                mag1 = (v1[0]**2 + v1[1]**2)**0.5
                mag2 = (v2[0]**2 + v2[1]**2)**0.5
                
                if mag1 * mag2 > 0:
                    cos_theta = dot / (mag1 * mag2)
                    if cos_theta < 0.8:  # Angle > ~36 degrees indicates a turn
                        turns += 1
                        
        return {
            "path": path,
            "geometry": geometry,
            "distance_meters": round(float(dist), 2),
            "turns": turns
        }
        
    except nx.NetworkXNoPath:
        return {"error": "No routable path exists between these locations due to network fragmentation"}


def k_shortest_paths(
    G: nx.Graph, 
    source: int, 
    target: int, 
    k: int = 3, 
    weight: str = 'weight'
) -> List[dict]:
    """Find K alternative routes between source and target."""
    if source not in G or target not in G:
        return [{"error": "Source or target not in graph"}]
        
    routes = []
    try:
        # Use simple paths generator sorted by length
        generator = nx.shortest_simple_paths(G, source, target, weight=weight)
        for i, path in enumerate(generator):
            if i >= k:
                break
                
            dist = sum(G[path[j]][path[j+1]].get(weight, 1.0) for j in range(len(path)-1))
            geometry = [list(G.nodes[node_id].get("pos", (0,0))) for node_id in path]
            
            routes.append({
                "route_index": i,
                "path": path,
                "geometry": geometry,
                "distance_meters": round(float(dist), 2),
                "turns": 0  # Simplified
            })
            
    except (nx.NetworkXNoPath, nx.NetworkXError):
        pass
        
    return routes


def reroute_after_failure(
    G: nx.Graph, 
    source: int, 
    target: int, 
    failed_nodes: List[int]
) -> dict:
    """Calculate detour overhead after a list of nodes fail."""
    original = shortest_path(G, source, target)
    rerouted = shortest_path(G, source, target, avoid_nodes=failed_nodes)
    
    if "error" in original:
        return {"error": f"Baseline error: {original['error']}"}
    if "error" in rerouted:
        return {
            "original_distance_m": original["distance_meters"],
            "rerouted_distance_m": float('inf'),
            "detour_factor": float('inf'),
            "isolated": True,
            "recommendation": "Destination isolated! Deploy emergency transit links."
        }
        
    detour = rerouted["distance_meters"] / original["distance_meters"] if original["distance_meters"] > 0 else 1.0
    
    return {
        "original_distance_m": original["distance_meters"],
        "rerouted_distance_m": rerouted["distance_meters"],
        "detour_factor": round(float(detour), 4),
        "isolated": False,
        "original_path": original["path"],
        "rerouted_path": rerouted["path"],
        "rerouted_geometry": rerouted["geometry"],
    }


def evacuation_routes(
    G: nx.Graph, 
    origin_polygon: tuple, 
    destinations: List[int]
) -> List[dict]:
    """
    Find best evacuation routes from all nodes in an origin area to nearest destinations.
    origin_polygon: (minx, miny, maxx, maxy) bounding box of origin zone
    """
    minx, miny, maxx, maxy = origin_polygon
    
    origins = []
    for node_id, attrs in G.nodes(data=True):
        lng = attrs.get("longitude", 0.0)
        lat = attrs.get("latitude", 0.0)
        if minx <= lng <= maxx and miny <= lat <= maxy:
            origins.append(node_id)
            
    routes = []
    for orig in origins:
        best_dist = float('inf')
        best_route = None
        
        for dest in destinations:
            if dest not in G:
                continue
            path_res = shortest_path(G, orig, dest)
            if "error" not in path_res and path_res["distance_meters"] < best_dist:
                best_dist = path_res["distance_meters"]
                best_route = path_res
                best_route["destination_node"] = dest
                best_route["origin_node"] = orig
                
        if best_route:
            routes.append(best_route)
            
    return routes
