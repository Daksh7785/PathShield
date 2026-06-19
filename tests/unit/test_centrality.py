"""
Unit tests for network centrality calculations and bottleneck detection.
"""
import networkx as nx
import pytest
from analysis.centrality import (
    calculate_betweenness_centrality,
    identify_bottlenecks,
    composite_criticality_score
)


def test_center_node_highest_centrality():
    """Verify that the center node of a star graph has the highest betweenness centrality."""
    # Star graph: center node is 0, connected to 1, 2, 3, 4
    G = nx.star_graph(4)
    
    # Initialize attributes
    for u, v in G.edges():
        G[u][v]['weight'] = 1.0
        
    scores = calculate_betweenness_centrality(G)
    
    # Node 0 must have the highest centrality (it bridges all pairs)
    assert scores[0] == max(scores.values())
    assert scores[0] > 0.0
    assert scores[1] == 0.0  # Outer nodes have no shortest paths passing through them


def test_scores_normalized_0_to_1():
    """Verify that all normalized composite criticality scores fall within [0, 1]."""
    G = nx.path_graph(10)
    for u, v in G.edges():
        G[u][v]['weight'] = 1.0
    for n in G.nodes():
        G.nodes[n]['betweenness_centrality'] = 0.1 * n
        G.nodes[n]['closeness_centrality'] = 0.2 * n
        
    scores = composite_criticality_score(G)
    
    for node_id, score in scores.items():
        assert 0.0 <= score <= 1.0, f"Score for node {node_id} is out of bounds: {score}"


def test_bottleneck_identification_top_10pct():
    """Verify that top percentile bottleneck identification selects the correct count of nodes."""
    # Create a 100 node path graph
    G = nx.path_graph(100)
    for u, v in G.edges():
        G[u][v]['weight'] = 1.0
        
    # Seed centrality values
    for n in G.nodes():
        G.nodes[n]['betweenness_centrality'] = float(n) # Higher node IDs are more critical
        
    bottlenecks = identify_bottlenecks(G, top_percentile=0.1)
    
    # 10% of 100 is 10 nodes
    assert len(bottlenecks) == 10
    # They should be the highest indexed nodes (90 to 99)
    assert min(bottlenecks) == 90
