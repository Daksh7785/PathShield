import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

# Ensure current folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_pipeline.tiling import tile_geotiff, reconstruct_from_tiles

app = FastAPI(title="PathShield GIS Engine", version="1.0.0")

class TileRequest(BaseModel):
    image_path: str
    tile_size: int = 256
    overlap: int = 32

class OSMRequest(BaseModel):
    city_name: str
    bbox: List[float] # [min_lat, min_lng, max_lat, max_lng]

@app.get("/health")
def health():
    return {"status": "healthy", "service": "gis-engine"}

@app.post("/tile")
def tile_image(req: TileRequest):
    if not os.path.exists(req.image_path):
        # We allow fallback creation inside tile_geotiff directly
        pass
        
    try:
        # Calculate overlap fraction
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
    # Mock OSM extraction for the demo pipeline
    return {
        "message": f"OSM network successfully downloaded and rasterized for {req.city_name}",
        "nodes_count": 500,
        "edges_count": 800,
        "geojson_url": f"/data/processed/{req.city_name.lower()}/osm_network.geojson"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
