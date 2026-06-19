"""
Integration tests executing the full pipeline from raw mask to graph and centrality.
"""
import numpy as np
import cv2
import networkx as nx

from topology.skeletonization import process_mask_to_skeleton
from topology.healing import heal_topology
from topology.graph_builder import skeleton_to_graph, graph_to_geojson
from analysis.centrality import calculate_betweenness_centrality
from analysis.stress_test import StressTestEngine


def test_pipeline_e2e():
    """Verify the entire pipeline runs sequentially without throwing errors."""
    # 1. Create synthetic satellite road mask (512x512)
    mask = np.zeros((512, 512), dtype=np.uint8)
    
    # Draw horizontal, vertical and diag roads (12px wide)
    cv2.line(mask, (0, 256), (512, 256), 255, 12)
    cv2.line(mask, (256, 0), (256, 512), 255, 12)
    cv2.line(mask, (0, 0), (512, 512), 255, 12)
    
    # Introduce a 20px gap in the vertical road
    mask[150:170, 250:262] = 0
    
    # 2. Skeletonize
    skeleton, nodes = process_mask_to_skeleton(mask)
    assert len(nodes['endpoints']) > 0, "No endpoints detected near the gap boundary"
    
    # 3. Heal topology
    healed = heal_topology(skeleton, nodes['endpoints'], nodes['junctions'], max_gap_px=40)
    
    # 4. Construct graph
    bounds = (77.45, 12.85, 77.75, 13.10)
    G = skeleton_to_graph(healed, nodes, bounds, city_id="test_city")
    
    assert G.number_of_nodes() > 0, "Graph has zero nodes"
    assert G.number_of_edges() > 0, "Graph has zero edges"
    
    # 5. Compute centrality
    calculate_betweenness_centrality(G)
    
    # 6. Run stress test
    engine = StressTestEngine(G)
    report = engine.full_vulnerability_report(top_n=3)
    
    for item in report:
        assert "resilience_index" in item
        assert "lcc_loss_percent" in item
        
    # 7. Export GeoJSON
    geojson = graph_to_geojson(G)
    assert geojson["type"] == "FeatureCollection"
    assert "features" in geojson
    assert len(geojson["features"]) > 0
