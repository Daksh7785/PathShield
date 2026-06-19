import os
import sys
import math
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Tuple

# Ensure current folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_pipeline.tiling import tile_geotiff, reconstruct_from_tiles
from data_pipeline.osm_rasterizer import download_osm_roads

app = FastAPI(title="PathShield GIS Engine", version="1.0.0")

class TileRequest(BaseModel):
    image_path: str
    tile_size: int = 256
    overlap: int = 32

class OSMRequest(BaseModel):
    city_name: str
    bbox: List[float] # [min_lat, min_lng, max_lat, max_lng]

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000  # radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def geojson_to_network(geojson_data: dict) -> Tuple[List[dict], List[dict]]:
    coord_to_id = {}
    nodes = []
    edges = []
    
    # Count frequency of each coordinate to find junctions
    coord_counts = {}
    for feature in geojson_data.get("features", []):
        geom = feature.get("geometry", {})
        if geom.get("type") == "LineString":
            coords = geom.get("coordinates", [])
            for c in coords:
                if len(c) >= 2:
                    t = (round(c[0], 6), round(c[1], 6))
                    coord_counts[t] = coord_counts.get(t, 0) + 1
                    
    node_id_counter = 1
    
    for feature in geojson_data.get("features", []):
        geom = feature.get("geometry", {})
        if geom.get("type") == "LineString":
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue
            
            current_path = []
            for i, c in enumerate(coords):
                if len(c) < 2:
                    continue
                t = (round(c[0], 6), round(c[1], 6))
                current_path.append(t)
                
                is_junction = coord_counts.get(t, 0) > 1
                is_endpoint = (i == 0 or i == len(coords) - 1)
                
                if (is_junction or is_endpoint) and len(current_path) > 1:
                    start_coord = current_path[0]
                    end_coord = current_path[-1]
                    
                    for pt in [start_coord, end_coord]:
                        if pt not in coord_to_id:
                            coord_to_id[pt] = node_id_counter
                            nodes.append({
                                "id": node_id_counter,
                                "longitude": pt[0],
                                "latitude": pt[1],
                                "node_type": "intersection" if coord_counts.get(pt, 0) > 1 else "endpoint",
                                "degree": 0,
                                "betweenness_centrality": 0.0,
                                "closeness_centrality": 0.0,
                                "is_gateway": False
                            })
                            node_id_counter += 1
                            
                    u = coord_to_id[start_coord]
                    v = coord_to_id[end_coord]
                    
                    if u != v:
                        dist = haversine_distance(start_coord[1], start_coord[0], end_coord[1], end_coord[0])
                        dist = max(5.0, dist)
                        edges.append({
                            "source": u,
                            "target": v,
                            "length_meters": round(dist, 2),
                            "confidence": 1.0,
                            "is_healing_edge": False
                        })
                    
                    current_path = [t]
                    
    for edge in edges:
        u, v = edge["source"], edge["target"]
        for node in nodes:
            if node["id"] in (u, v):
                node["degree"] += 1
                
    for node in nodes:
        node["is_gateway"] = (node["degree"] == 1)
        
    return nodes, edges

def generate_fallback_network(bounds: tuple) -> Tuple[List[dict], List[dict]]:
    minx, miny, maxx, maxy = bounds
    nodes = []
    edges = []
    cols = 8
    rows = 8
    
    x_coords = [minx + (i * (maxx - minx)) / (cols - 1) for i in range(cols)]
    y_coords = [miny + (i * (maxy - miny)) / (rows - 1) for i in range(rows)]
    
    for r in range(rows):
        for c in range(cols):
            id_ = r * cols + c + 1
            nodes.append({
                "id": id_,
                "longitude": x_coords[c],
                "latitude": y_coords[r],
                "node_type": "intersection" if (r % 2 == 0 and c % 2 == 0) else "endpoint",
                "degree": 0,
                "betweenness_centrality": 0.0,
                "closeness_centrality": 0.0,
                "is_gateway": False
            })
            
    for r in range(rows):
        for c in range(cols):
            curr = r * cols + c + 1
            if c + 1 < cols:
                dist = haversine_distance(y_coords[r], x_coords[c], y_coords[r], x_coords[c+1])
                edges.append({
                    "source": curr,
                    "target": curr + 1,
                    "length_meters": round(max(5.0, dist), 2),
                    "confidence": 1.0,
                    "is_healing_edge": False
                })
            if r + 1 < rows:
                dist = haversine_distance(y_coords[r], x_coords[c], y_coords[r+1], x_coords[c])
                edges.append({
                    "source": curr,
                    "target": curr + cols,
                    "length_meters": round(max(5.0, dist), 2),
                    "confidence": 1.0,
                    "is_healing_edge": False
                })
                
    for edge in edges:
        u, v = edge["source"], edge["target"]
        for node in nodes:
            if node["id"] in (u, v):
                node["degree"] += 1
        
    for n in nodes:
        n["is_gateway"] = (n["degree"] == 1)
        
    return nodes, edges

@app.get("/health")
def health():
    return {"status": "healthy", "service": "gis-engine"}

@app.post("/tile")
def tile_image(req: TileRequest):
    if not os.path.exists(req.image_path):
        pass
        
    try:
        overlap_fraction = float(req.overlap) / float(req.tile_size) if req.tile_size > 0 else 0.5
        output_dir = "data/processed/tiles"
        
        tiles_meta = tile_geotiff(
            input_path=req.image_path,
            output_dir=output_dir,
            tile_size=req.tile_size,
            overlap=overlap_fraction
        )
        return {
            "message": "Tiling completed successfully",
            "tile_count": len(tiles_meta.get("tiles", [])),
            "tiles": tiles_meta.get("tiles", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tiling failed: {str(e)}")

@app.post("/osm")
def fetch_osm(req: OSMRequest):
    if not req.bbox or len(req.bbox) != 4:
        raise HTTPException(status_code=400, detail="bbox must be a list of 4 float coordinates: [min_lat, min_lng, max_lat, max_lng]")
        
    min_lat, min_lng, max_lat, max_lng = req.bbox
    bounds = (min_lng, min_lat, max_lng, max_lat)
    
    output_geojson_path = f"data/processed/{req.city_name.lower()}/osm_network.geojson"
    
    try:
        download_osm_roads(bounds, output_geojson_path)
        
        if os.path.exists(output_geojson_path):
            with open(output_geojson_path) as f:
                geojson_data = json.load(f)
            
            features = geojson_data.get("features", [])
            if len(features) > 0:
                nodes, edges = geojson_to_network(geojson_data)
                if len(nodes) > 0:
                    return {
                        "message": f"OSM network successfully downloaded and processed for {req.city_name}",
                        "name": req.city_name,
                        "nodes": nodes,
                        "edges": edges,
                        "total_nodes": len(nodes),
                        "total_edges": len(edges)
                    }
    except Exception as e:
        print(f"OSM download/processing failed: {e}. Falling back to dynamic synthetic grid.")
        
    nodes, edges = generate_fallback_network(bounds)
    return {
        "message": f"OSM network download failed or is offline. Generated dynamic resilient spatial grid for {req.city_name}",
        "name": req.city_name,
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

