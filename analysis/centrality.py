"""
Centrality calculation functions for identifying critical road intersections
and network bottlenecks in the urban road graph.
"""
import networkx as nx
import numpy as np
from typing import Dict, List


def calculate_betweenness_centrality(
    G: nx.Graph, 
    normalized: bool = True, 
    weight: str = 'weight'
) -> Dict[int, float]:
    """
    Calculate Betweenness Centrality for all nodes in the graph.
    Uses Brandes' algorithm under the hood via NetworkX.
    
    Args:
        G: NetworkX Graph
        normalized: Whether to normalize by the number of node pairs
        weight: Edge weight attribute for path lengths
        
    Returns:
        Dict mapping node_id to betweenness centrality score
    """
    print("Calculating betweenness centrality (Brandes' algorithm)...")
    
    # Brandes algorithm runs. For large graphs, this can be slow.
    scores = nx.betweenness_centrality(G, normalized=normalized, weight=weight)
    
    # Write back to nodes
    for node_id, score in scores.items():
        G.nodes[node_id]['betweenness_centrality'] = float(score)
        
    # Print top 5
    sorted_nodes = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    print("Top 5 bottleneck nodes by betweenness centrality:")
    for rank, (node_id, score) in enumerate(sorted_nodes[:5]):
        print(f"  Rank {rank+1}: Node {node_id} | Score: {score:.6f}")
        
    return scores


def calculate_closeness_centrality(G: nx.Graph) -> Dict[int, float]:
    """Calculate Closeness Centrality for all nodes in the graph."""
    print("Calculating closeness centrality...")
    scores = nx.closeness_centrality(G, distance='weight')
    
    for node_id, score in scores.items():
        G.nodes[node_id]['closeness_centrality'] = float(score)
        
    return scores


def identify_bottlenecks(G: nx.Graph, top_percentile: float = 0.1) -> List[int]:
    """
    Identify the top-N% of nodes by betweenness centrality and mark them as gateways.
    
    Returns:
        List of node IDs that are bottlenecks.
    """
    scores = {node_id: G.nodes[node_id].get('betweenness_centrality', 0.0) for node_id in G.nodes()}
    if not scores:
        return []
        
    n_nodes = len(scores)
    n_top = max(1, int(n_nodes * top_percentile))
    
    sorted_nodes = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    bottlenecks = [node_id for node_id, _ in sorted_nodes[:n_top]]
    
    # Mark gateways
    for node_id in G.nodes():
        G.nodes[node_id]['is_gateway'] = (node_id in bottlenecks)
        
    print(f"✓ Marked {len(bottlenecks)} nodes as gateways (top {top_percentile*100:.1f}%)")
    return bottlenecks


def composite_criticality_score(G: nx.Graph) -> Dict[int, float]:
    """
    Compute a composite criticality score combining:
    - Betweenness centrality (0.6)
    - Degree centrality (0.2)
    - Closeness centrality (0.2)
    
    Scores are normalized to [0, 1] range.
    Writes 'criticality_score' and 'criticality_rank' as node attributes.
    """
    print("Calculating composite criticality scores...")
    n_nodes = len(G)
    if n_nodes == 0:
        return {}
        
    # Calculate degree centrality
    deg_centrality = nx.degree_centrality(G)
    
    # Ensure betweenness and closeness are computed
    for n in G.nodes():
        if 'betweenness_centrality' not in G.nodes[n]:
            G.nodes[n]['betweenness_centrality'] = 0.0
        if 'closeness_centrality' not in G.nodes[n]:
            # Basic fallback
            G.nodes[n]['closeness_centrality'] = float(deg_centrality[n])
            
    raw_scores = {}
    for n in G.nodes():
        bc = G.nodes[n]['betweenness_centrality']
        cc = G.nodes[n]['closeness_centrality']
        dc = deg_centrality[n]
        
        # Weighted sum
        raw_scores[n] = 0.6 * bc + 0.2 * cc + 0.2 * dc
        
    # Normalize to [0, 1]
    min_score = min(raw_scores.values()) if raw_scores else 0.0
    max_score = max(raw_scores.values()) if raw_scores else 1.0
    score_range = max_score - min_score
    if score_range == 0:
        score_range = 1.0
        
    norm_scores = {n: float((s - min_score) / score_range) for n, s in raw_scores.items()}
    
    # Write back to nodes
    for n, s in norm_scores.items():
        G.nodes[n]['criticality_score'] = s
        
    # Rank nodes (1 = most critical)
    sorted_nodes = sorted(norm_scores.items(), key=lambda item: item[1], reverse=True)
    for rank, (node_id, _) in enumerate(sorted_nodes):
        G.nodes[node_id]['criticality_rank'] = rank + 1
        
    return norm_scores


def refresh_city_centrality(G: nx.Graph, city_id: str) -> dict:
    """Run all centrality metrics and return summary statistics."""
    calculate_betweenness_centrality(G)
    calculate_closeness_centrality(G)
    identify_bottlenecks(G, top_percentile=0.1)
    scores = composite_criticality_score(G)
    
    avg_score = np.mean(list(scores.values())) if scores else 0.0
    max_score = np.max(list(scores.values())) if scores else 0.0
    
    return {
        "city_id": city_id,
        "avg_criticality": round(float(avg_score), 4),
        "max_criticality": round(float(max_score), 4),
        "total_nodes": G.number_of_nodes(),
    }
