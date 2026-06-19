"""
Pre-defined disaster scenario catalog (flooding, earthquake, peak traffic)
used for structural network ablation stress testing.
"""
import networkx as nx
import numpy as np
from typing import List, Dict, Optional, Tuple

from analysis.stress_test import StressTestEngine


class ScenarioLibrary:
    
    @staticmethod
    def equipment_failure(G: nx.Graph, n_nodes: int = 1) -> List[int]:
        """Simulate random failure of n network nodes."""
        rng = np.random.default_rng()
        nodes = list(G.nodes())
        if not nodes:
            return []
        return list(rng.choice(nodes, size=min(n_nodes, len(nodes)), replace=False))

    @staticmethod
    def flood_zone(G: nx.Graph, bounds: Tuple[float, float, float, float]) -> List[int]:
        """Identify all nodes inside the bounding box of a flooded area."""
        minx, miny, maxx, maxy = bounds
        flooded = []
        for n, attrs in G.nodes(data=True):
            lng = attrs.get("longitude", 0.0)
            lat = attrs.get("latitude", 0.0)
            if minx <= lng <= maxx and miny <= lat <= maxy:
                flooded.append(n)
        return flooded

    @staticmethod
    def earthquake_damage(
        G: nx.Graph, 
        epicenter: Tuple[float, float], 
        radius_degrees: float = 0.015
    ) -> List[int]:
        """Simulate radial earthquake damage around a centerpoint."""
        ex, ey = epicenter
        damaged = []
        for n, attrs in G.nodes(data=True):
            lng = attrs.get("longitude", 0.0)
            lat = attrs.get("latitude", 0.0)
            dist = np.sqrt((lng - ex)**2 + (lat - ey)**2)
            if dist <= radius_degrees:
                damaged.append(n)
        return damaged

    @staticmethod
    def peak_traffic_stress(G: nx.Graph, percentile: float = 0.2) -> List[int]:
        """Identify top-N% highest betweenness centrality nodes under peak traffic load."""
        scores = {node_id: G.nodes[node_id].get('betweenness_centrality', 0.0) for node_id in G.nodes()}
        sorted_nodes = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        n_cut = max(1, int(len(G) * percentile))
        return [n for n, _ in sorted_nodes[:n_cut]]


def run_scenario(G: nx.Graph, scenario_name: str, **kwargs) -> dict:
    """
    Execute a scenario and compute resilience index impact.
    
    Returns:
        {
          "scenario": str,
          "affected_nodes": list,
          "lcc_loss": float,
          "path_increase": float,
          "resilience_index": float,
          "recommendations": str
        }
    """
    engine = StressTestEngine(G)
    affected_nodes = []
    
    if scenario_name == "equipment_failure":
        n = kwargs.get("n_nodes", 1)
        affected_nodes = ScenarioLibrary.equipment_failure(G, n_nodes=n)
    elif scenario_name == "flood":
        bounds = kwargs.get("bounds", (0.0, 0.0, 0.0, 0.0))
        affected_nodes = ScenarioLibrary.flood_zone(G, bounds)
    elif scenario_name == "earthquake":
        epicenter = kwargs.get("epicenter", (0.0, 0.0))
        rad = kwargs.get("radius", 0.015)
        affected_nodes = ScenarioLibrary.earthquake_damage(G, epicenter, radius_degrees=rad)
    elif scenario_name == "peak_traffic":
        pct = kwargs.get("percentile", 0.2)
        affected_nodes = ScenarioLibrary.peak_traffic_stress(G, percentile=pct)
    else:
        return {"error": f"Scenario {scenario_name} is not registered in the library"}
        
    res = engine.ablate_nodes(affected_nodes)
    
    return {
        "scenario": scenario_name,
        "affected_nodes_count": len(affected_nodes),
        "affected_nodes": [int(n) for n in affected_nodes],
        "lcc_loss": res["lcc_loss_percent"],
        "path_increase": res["path_increase_factor"],
        "resilience_index": res["resilience_index"],
        "recommendations": res["recommendation_text"]
    }
