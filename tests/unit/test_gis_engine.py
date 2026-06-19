import pytest
import sys
import os
import importlib.util
from fastapi.testclient import TestClient

# Load gis-engine main.py directly
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../gis-engine/main.py'))
spec = importlib.util.spec_from_file_location("gis_main", module_path)
gis_main = importlib.util.module_from_spec(spec)
sys.modules["gis_main"] = gis_main
spec.loader.exec_module(gis_main)

app = gis_main.app
geojson_to_network = gis_main.geojson_to_network
generate_fallback_network = gis_main.generate_fallback_network
haversine_distance = gis_main.haversine_distance

client = TestClient(app)

def test_haversine_distance():
    # Distance between two points in Bengaluru
    dist = haversine_distance(12.9716, 77.5946, 12.9716, 77.6046)
    assert 1000.0 < dist < 1200.0

def test_generate_fallback_network():
    bounds = (77.45, 12.90, 77.55, 13.00)
    nodes, edges = generate_fallback_network(bounds)
    assert len(nodes) == 64  # 8x8 grid
    assert len(edges) > 100
    for node in nodes:
        assert "longitude" in node
        assert "latitude" in node
        assert "degree" in node
        assert "node_type" in node

def test_fetch_osm_endpoint():
    payload = {
        "city_name": "TestDynamicCity",
        "bbox": [12.90, 77.45, 13.00, 77.55]
    }
    response = client.post("/osm", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0
    assert data["name"] == "TestDynamicCity"

