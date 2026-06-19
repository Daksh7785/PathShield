"""
Unit tests for network stress testing, node ablation, and resilience index math.
"""
import networkx as nx
import pytest
from analysis.stress_test import StressTestEngine


def test_baseline_computed_on_init(synthetic_graph):
    """Verify that baseline values are properly generated when initializing the engine."""
    engine = StressTestEngine(synthetic_graph)
    
    assert "lcc_size" in engine._baseline
    assert "avg_path_length" in engine._baseline
    assert "network_efficiency" in engine._baseline
    
    # 10x10 grid has 100 nodes
    assert engine._baseline["lcc_size"] == 100
    assert engine._baseline["avg_path_length"] > 0.0


def test_ablation_returns_expected_keys(stress_engine):
    """Verify that single node ablation output has all required keys."""
    res = stress_engine.ablate_node(0) # ablate node 0
    
    assert "lcc_loss_percent" in res
    assert "path_increase_factor" in res
    assert "resilience_index" in res
    assert "critical" in res
    assert "recommendation_text" in res


def test_bridge_node_removal_critical():
    """Verify that removing a critical bridge node drops the resilience index dramatically."""
    # Create two disconnected clusters connected by a single bridge node:
    # Cluster A (0,1,2) + Bridge (3) + Cluster B (4,5,6)
    G = nx.Graph()
    G.add_edges_from([(0,1), (1,2), (2,3), (3,4), (4,5), (5,6)])
    
    # Initialize edge weights
    for u, v in G.edges():
        G[u][v]['weight'] = 1.0
        
    engine = StressTestEngine(G)
    
    # Ablate the bridge node 3
    res = engine.ablate_node(3)
    
    # Resilience index should be very low (since the graph splits into two disconnected clusters)
    assert res["resilience_index"] < 0.5
    assert res["critical"] is True


def test_resilience_index_clipped_0_to_1(stress_engine):
    """Verify that the resilience index is bounded within [0.0, 1.0]."""
    # Test clipping with mock values
    r1 = stress_engine.resilience_index(10.0, 5.0)  # Path decreased (resilience > 1.0)
    assert r1 == 1.0, f"Expected clipped index of 1.0, got {r1}"
    
    r2 = stress_engine.resilience_index(10.0, float('inf')) # Disconnected path
    assert r2 == 0.0, f"Expected index of 0.0, got {r2}"
