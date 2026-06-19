"""
Convert OpenStreetMap vector data (GeoJSON/OSM) to binary road mask GeoTIFFs.
Used to generate ground truth for training.
"""
import json
import numpy as np
import cv2
from shapely.geometry import shape, mapping
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.parse


def osm_geojson_to_mask(
    geojson_path: str,
    bounds: tuple,
    output_path: str,
    width: int = 256,
    height: int = 256,
    road_types: Optional[list] = None,
    line_thickness: int = 3
) -> np.ndarray:
    """
    Rasterize OSM road GeoJSON to binary mask.
    
    Args:
        geojson_path: Path to GeoJSON with road LineStrings
        bounds: (minx, miny, maxx, maxy) geographic bounds for this tile
        output_path: Where to save the binary PNG mask
        width, height: Output raster dimensions (should match tile size)
        road_types: Filter by OSM highway types (None = all)
        line_thickness: Road line width in pixels
    
    Returns:
        Binary numpy array (H, W) with roads=255, background=0
    """
    if road_types is None:
        road_types = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary',
                      'residential', 'unclassified', 'service', 'motorway_link',
                      'trunk_link', 'primary_link', 'secondary_link']

    minx, miny, maxx, maxy = bounds
    x_scale = width / (maxx - minx) if (maxx - minx) != 0 else 1.0
    y_scale = height / (maxy - miny) if (maxy - miny) != 0 else 1.0

    mask = np.zeros((height, width), dtype=np.uint8)

    if not Path(geojson_path).exists():
        # Draw fake road for testing if GeoJSON missing
        print(f"⚠ GeoJSON {geojson_path} not found. Drawing a default synthetic road in mask.")
        cv2.line(mask, (0, height // 2), (width, height // 2), 255, line_thickness)
        cv2.imwrite(output_path, mask)
        return mask

    with open(geojson_path) as f:
        data = json.load(f)

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        highway = props.get("highway", "")
        if highway not in road_types:
            continue

        geom = feature.get("geometry", {})
        geom_type = geom.get("type", "")

        if geom_type == "LineString":
            lines = [geom["coordinates"]]
        elif geom_type == "MultiLineString":
            lines = geom["coordinates"]
        else:
            continue

        for line in lines:
            pts = []
            for lon, lat in line:
                px = int((lon - minx) * x_scale)
                py = int((maxy - lat) * y_scale)
                if 0 <= px < width and 0 <= py < height:
                    pts.append([px, py])
            
            if len(pts) >= 2:
                cv2.polylines(mask, [np.array(pts, dtype=np.int32)],
                              isClosed=False, color=255, thickness=line_thickness)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_path, mask)
    return mask


def download_osm_roads(bounds: tuple, output_path: str) -> str:
    """
    Download road data from Overpass API for given bounds.
    bounds: (minx, miny, maxx, maxy) in WGS84
    """
    minx, miny, maxx, maxy = bounds
    query = f"""
    [out:json][timeout:60];
    (
      way["highway"]({miny},{minx},{maxy},{maxx});
    );
    out geom;
    """
    
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": query}).encode()
    
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            osm_data = json.loads(resp.read())
    except Exception as e:
        print(f"❌ Failed to fetch from Overpass API: {e}. Writing empty GeoJSON.")
        osm_data = {"elements": []}
    
    # Convert to GeoJSON
    features = []
    for element in osm_data.get("elements", []):
        if element["type"] == "way" and "geometry" in element:
            coords = [[n["lon"], n["lat"]] for n in element["geometry"]]
            features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": element.get("tags", {})
            })
    
    geojson = {"type": "FeatureCollection", "features": features}
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(geojson, f)
    
    print(f"✓ Downloaded {len(features)} road features → {output_path}")
    return output_path
