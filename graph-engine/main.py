import os
import sys
import base64
from io import BytesIO
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Tuple
import numpy as np
from PIL import Image
import networkx as nx

# Ensure current folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from topology.skeletonization import process_mask_to_skeleton, extract_graph_nodes
from topology.healing import heal_topology
from topology.graph_builder import skeleton_to_graph
from analysis.centrality import calculate_betweenness_centrality, calculate_closeness_centrality
from analysis.stress_test import StressTestEngine
from analysis.routing import shortest_path, k_shortest_paths

app = FastAPI(title="PathShield Graph Engine", version="1.0.0")

class SkeletonizeRequest(BaseModel):
    mask_base64: str

class HealRequest(BaseModel):
    skeleton_base64: str
    max_gap_meters: float = 150.0
    angle_tolerance_deg: float = 45.0

class CentralityRequest(BaseModel):
    graph_json: Dict

class StressTestRequest(BaseModel):
    graph_json: Dict
    scenario_type: str # "flood", "accident", "ablation", "cascading", "random"
    ablate_nodes: Optional[List[int]] = None
    flood_bounds: Optional[List[float]] = None # [minx, miny, maxx, maxy]
    seed_node: Optional[int] = None
    iterations: Optional[int] = 5
    failure_probability: Optional[float] = 0.1

class RouteRequest(BaseModel):
    graph_json: Dict
    source_node: int
    target_node: int
    disabled_nodes: Optional[List[int]] = None
    disabled_edges: Optional[List[List[int]]] = None
    traffic_congestion: Optional[Dict[str, float]] = None

def _deserialize_graph(graph_json: Dict) -> nx.Graph:
    """Helper to convert dictionary back to NetworkX Graph."""
    G = nx.Graph()
    for n in graph_json.get("nodes", []):
        G.add_node(n["id"], **n)
    for e in graph_json.get("edges", []):
        G.add_edge(e["source"], e["target"], **e)
    return G

def _serialize_graph(G: nx.Graph) -> Dict:
    """Helper to convert NetworkX Graph to serializable dictionary."""
    nodes = []
    for n, attrs in G.nodes(data=True):
        node_attr = attrs.copy()
        node_attr["id"] = n
        nodes.append(node_attr)
    edges = []
    for u, v, attrs in G.edges(data=True):
        edge_attr = attrs.copy()
        edge_attr["source"] = u
        edge_attr["target"] = v
        edges.append(edge_attr)
    return {"nodes": nodes, "edges": edges}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "graph-engine"}

@app.post("/skeletonize")
def skeletonize(req: SkeletonizeRequest):
    try:
        img_data = base64.b64decode(req.mask_base64)
        img = Image.open(BytesIO(img_data)).convert("L")
        mask_np = np.array(img)
        
        skeleton, nodes = process_mask_to_skeleton(mask_np)
        junctions = nodes.get("junctions", [])
        endpoints = nodes.get("endpoints", [])
        
        skel_pil = Image.fromarray((skeleton * 255).astype(np.uint8))
        skel_buffer = BytesIO()
        skel_pil.save(skel_buffer, format="PNG")
        skel_b64 = base64.b64encode(skel_buffer.getvalue()).decode("utf-8")
        
        return {
            "skeleton_base64": skel_b64,
            "junctions_count": len(junctions),
            "endpoints_count": len(endpoints)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skeletonization failed: {str(e)}")

@app.post("/heal")
def heal(req: HealRequest):
    try:
        img_data = base64.b64decode(req.skeleton_base64)
        img = Image.open(BytesIO(img_data)).convert("L")
        skeleton_np = np.array(img)
        
        # Extact nodes and heal
        nodes = extract_graph_nodes(skeleton_np)
        healed_skeleton = heal_topology(skeleton_np, nodes["endpoints"], nodes["junctions"])
        healed_nodes = extract_graph_nodes(healed_skeleton)
        
        # Build healed graph
        bounds = (77.45, 12.85, 77.75, 13.10)
        G_healed = skeleton_to_graph(healed_skeleton, healed_nodes, bounds, city_id="temp")
        
        return {
            "healed_graph": _serialize_graph(G_healed),
            "healed_edges_added": G_healed.number_of_edges()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Healing failed: {str(e)}")

@app.post("/centrality")
def centrality(req: CentralityRequest):
    try:
        G = _deserialize_graph(req.graph_json)
        bc_scores = calculate_betweenness_centrality(G)
        cc_scores = calculate_closeness_centrality(G)
        
        # Save scores to nodes
        for node_id in G.nodes():
            G.nodes[node_id]["betweenness_centrality"] = bc_scores.get(node_id, 0.0)
            G.nodes[node_id]["closeness_centrality"] = cc_scores.get(node_id, 0.0)
            
        return {
            "graph": _serialize_graph(G),
            "top_bottlenecks": sorted(bc_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Centrality computation failed: {str(e)}")

@app.post("/stress-test")
def stress_test(req: StressTestRequest):
    try:
        G = _deserialize_graph(req.graph_json)
        engine = StressTestEngine(G)
        
        if req.scenario_type == "ablation":
            if not req.ablate_nodes or len(req.ablate_nodes) == 0:
                raise HTTPException(status_code=400, detail="ablate_nodes is required for ablation scenario")
            if len(req.ablate_nodes) == 1:
                results = engine.ablate_node(req.ablate_nodes[0])
            else:
                results = engine.ablate_nodes(req.ablate_nodes)
        elif req.scenario_type == "flood":
            if not req.flood_bounds or len(req.flood_bounds) != 4:
                raise HTTPException(status_code=400, detail="flood_bounds is required as [minx, miny, maxx, maxy]")
            results = engine.flood_scenario(tuple(req.flood_bounds))
        elif req.scenario_type == "cascading":
            if req.seed_node is None:
                raise HTTPException(status_code=400, detail="seed_node is required for cascading failure")
            results = engine.cascading_failure(req.seed_node, req.iterations)
        elif req.scenario_type == "random":
            results = engine.random_failure(req.failure_probability)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown scenario_type: {req.scenario_type}")
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stress testing failed: {str(e)}")

@app.post("/route")
def route(req: RouteRequest):
    try:
        G = _deserialize_graph(req.graph_json)
        
        # Apply traffic congestion weights
        if req.traffic_congestion:
            for edge_str, multiplier in req.traffic_congestion.items():
                try:
                    parts = edge_str.split('-')
                    if len(parts) == 2:
                        u, v = int(parts[0]), int(parts[1])
                        if G.has_edge(u, v):
                            orig_weight = G[u][v].get('length_meters', G[u][v].get('weight', 150.0))
                            scaled_weight = orig_weight * multiplier
                            G[u][v]['weight'] = scaled_weight
                            G[u][v]['length_meters'] = scaled_weight
                except Exception as ex:
                    print(f"Error scaling edge {edge_str}: {ex}")
                    
        # Apply road closure (disabled edges) removal
        if req.disabled_edges:
            for edge in req.disabled_edges:
                if len(edge) == 2:
                    u, v = edge[0], edge[1]
                    if G.has_edge(u, v):
                        G.remove_edge(u, v)
        
        # Calculate shortest path
        res = shortest_path(G, req.source_node, req.target_node, avoid_nodes=req.disabled_nodes)
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
            
        path_list = res.get("path", [])
        dist = res.get("distance_meters", 0.0)
        
        # Calculate alternative path (k-shortest paths index 1)
        alt_routes = k_shortest_paths(G, req.source_node, req.target_node, k=2)
        alt_path_list = []
        alt_dist = 0.0
        
        if len(alt_routes) > 1 and "error" not in alt_routes[1]:
            alt_path_list = alt_routes[1].get("path", [])
            alt_dist = alt_routes[1].get("distance_meters", 0.0)
            
        return {
            "shortest_path": path_list,
            "distance_meters": dist,
            "alternative_path": alt_path_list,
            "alternative_distance_meters": alt_dist
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
