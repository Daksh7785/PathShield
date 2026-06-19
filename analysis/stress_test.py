"""
Stress testing engine for conducting node-ablation, flooding,
and cascading failure simulations on road graphs.
"""
import networkx as nx
import numpy as np
from typing import List, Dict, Optional


def generate_recommendation(resilience_index: float) -> str:
    """Generate recommendations based on resilience index values."""
    if resilience_index < 0.5:
        return "CRITICAL — immediate redundancy required. Add parallel route within 500m."
    elif 0.5 <= resilience_index < 0.7:
        return "HIGH RISK — schedule infrastructure hardening within 6 months."
    elif 0.7 <= resilience_index < 0.85:
        return "MODERATE — consider adding alternate route for peak traffic."
    else:
        return "LOW RISK — monitor as part of regular maintenance cycle."


class StressTestEngine:
    def __init__(self, G: nx.Graph):
        self.G = G.copy()
        self._baseline = self._compute_baseline()
    
    def _compute_baseline(self) -> dict:
        """Compute baseline metrics for the intact network."""
        lcc = max(nx.connected_components(self.G), key=len, default=set())
        G_lcc = self.G.subgraph(lcc).copy()
        
        try:
            # Get average path length of largest connected component
            avg_path = nx.average_shortest_path_length(G_lcc, weight='weight')
        except nx.NetworkXError:
            avg_path = float('inf')
        except Exception:
            avg_path = 0.0
        
        efficiency = nx.global_efficiency(self.G)
        
        return {
            "lcc_size": len(lcc),
            "total_nodes": self.G.number_of_nodes(),
            "avg_path_length": round(float(avg_path), 4) if avg_path != float('inf') else float('inf'),
            "network_efficiency": round(float(efficiency), 6),
        }
    
    def resilience_index(self, baseline_path: float, perturbed_path: float, lcc_fraction: float = 1.0) -> float:
        """R = (baseline / perturbed) * lcc_fraction. Lower = more vulnerable. Clipped to [0,1]."""
        if baseline_path == float('inf') or perturbed_path == float('inf') or perturbed_path == 0:
            return 0.0
        path_ratio = min(baseline_path / perturbed_path, 1.0)
        return round(path_ratio * lcc_fraction, 4)
        
    def ablate_node(self, node_id: int) -> dict:
        """Remove one node and measure impact."""
        if node_id not in self.G:
            return {"error": "Node not in graph"}
            
        G_perturbed = self.G.copy()
        G_perturbed.remove_node(node_id)
        
        lcc = max(nx.connected_components(G_perturbed), key=len, default=set())
        G_lcc = G_perturbed.subgraph(lcc).copy()
        
        try:
            perturbed_path = nx.average_shortest_path_length(G_lcc, weight='weight')
        except Exception:
            perturbed_path = float('inf')
            
        perturbed_efficiency = nx.global_efficiency(G_perturbed)
        
        baseline_path = self._baseline["avg_path_length"]
        lcc_fraction = len(lcc) / self._baseline["lcc_size"] if self._baseline["lcc_size"] > 0 else 1.0
        r_index = self.resilience_index(baseline_path, perturbed_path, lcc_fraction)
        
        # Calculate LCC loss percent
        lcc_loss_pct = 100.0 * (self._baseline["lcc_size"] - len(lcc)) / self._baseline["lcc_size"] if self._baseline["lcc_size"] > 0 else 0.0
        path_increase = perturbed_path / baseline_path if (baseline_path > 0 and perturbed_path != float('inf')) else float('inf')
        
        return {
            "removed_node_id": node_id,
            "baseline_lcc_size": self._baseline["lcc_size"],
            "perturbed_lcc_size": len(lcc),
            "lcc_loss_percent": round(lcc_loss_pct, 3),
            "baseline_avg_path_length": baseline_path,
            "perturbed_avg_path_length": perturbed_path,
            "path_increase_factor": round(path_increase, 4) if path_increase != float('inf') else float('inf'),
            "baseline_efficiency": self._baseline["network_efficiency"],
            "perturbed_efficiency": round(float(perturbed_efficiency), 6),
            "resilience_index": r_index,
            "critical": r_index < 0.7,
            "recommendation_text": generate_recommendation(r_index)
        }
    
    def ablate_nodes(self, node_ids: List[int]) -> dict:
        """Remove multiple nodes simultaneously and measure impact."""
        G_perturbed = self.G.copy()
        nodes_removed = [n for n in node_ids if n in G_perturbed]
        G_perturbed.remove_nodes_from(nodes_removed)
        
        lcc = max(nx.connected_components(G_perturbed), key=len, default=set())
        G_lcc = G_perturbed.subgraph(lcc).copy()
        
        try:
            perturbed_path = nx.average_shortest_path_length(G_lcc, weight='weight')
        except Exception:
            perturbed_path = float('inf')
            
        perturbed_efficiency = nx.global_efficiency(G_perturbed)
        
        baseline_path = self._baseline["avg_path_length"]
        lcc_fraction = len(lcc) / self._baseline["lcc_size"] if self._baseline["lcc_size"] > 0 else 1.0
        r_index = self.resilience_index(baseline_path, perturbed_path, lcc_fraction)
        lcc_loss_pct = 100.0 * (self._baseline["lcc_size"] - len(lcc)) / self._baseline["lcc_size"] if self._baseline["lcc_size"] > 0 else 0.0
        path_increase = perturbed_path / baseline_path if (baseline_path > 0 and perturbed_path != float('inf')) else float('inf')
        
        return {
            "removed_node_count": len(nodes_removed),
            "baseline_lcc_size": self._baseline["lcc_size"],
            "perturbed_lcc_size": len(lcc),
            "lcc_loss_percent": round(lcc_loss_pct, 3),
            "baseline_avg_path_length": baseline_path,
            "perturbed_avg_path_length": perturbed_path,
            "path_increase_factor": round(path_increase, 4) if path_increase != float('inf') else float('inf'),
            "baseline_efficiency": self._baseline["network_efficiency"],
            "perturbed_efficiency": round(float(perturbed_efficiency), 6),
            "resilience_index": r_index,
            "critical": r_index < 0.7,
            "recommendation_text": generate_recommendation(r_index)
        }
    
    def flood_scenario(self, polygon_bounds: tuple) -> dict:
        """
        Simulate flood: remove all nodes within geographic bounds.
        polygon_bounds: (minx, miny, maxx, maxy)
        """
        minx, miny, maxx, maxy = polygon_bounds
        
        nodes_to_remove = []
        for node_id, attrs in self.G.nodes(data=True):
            lng = attrs.get("longitude", 0.0)
            lat = attrs.get("latitude", 0.0)
            if minx <= lng <= maxx and miny <= lat <= maxy:
                nodes_to_remove.append(node_id)
                
        results = self.ablate_nodes(nodes_to_remove)
        results["affected_nodes_count"] = len(nodes_to_remove)
        results["scenario_type"] = "flood"
        
        return results
    
    def cascading_failure(self, seed_node: int, iterations: int = 5) -> dict:
        """
        Simulate cascading failure: remove seed node, recalculate centralities,
        and remove the new most critical neighbor or adjacent node iteratively.
        """
        G_temp = self.G.copy()
        failures = []
        
        current_node = seed_node
        for i in range(iterations):
            if current_node not in G_temp:
                break
                
            failures.append(int(current_node))
            neighbors = list(G_temp.neighbors(current_node))
            G_temp.remove_node(current_node)
            
            if not neighbors:
                # Fallback to highest centrality node remaining
                remaining = list(G_temp.nodes())
                if not remaining:
                    break
                current_node = remaining[0]
            else:
                # Pick neighbor with highest degree in remaining graph
                degrees = [G_temp.degree(nb) for nb in neighbors if nb in G_temp]
                if not degrees:
                    break
                current_node = neighbors[np.argmax(degrees)]
                
        results = self.ablate_nodes(failures)
        results["scenario_type"] = "cascading"
        results["failures_sequence"] = failures
        
        return results
    
    def random_failure(self, failure_probability: float, n_simulations: int = 100) -> dict:
        """
        Monte Carlo simulation of random node failures.
        Returns mean + std of resilience index across simulations.
        """
        res_indices = []
        n_nodes = self.G.number_of_nodes()
        
        for _ in range(n_simulations):
            to_remove = [node_id for node_id in self.G.nodes() if np.random.random() < failure_probability]
            res = self.ablate_nodes(to_remove)
            res_indices.append(res["resilience_index"])
            
        return {
            "scenario_type": "random",
            "failure_probability": failure_probability,
            "n_simulations": n_simulations,
            "mean_resilience_index": round(float(np.mean(res_indices)), 4),
            "std_resilience_index": round(float(np.std(res_indices)), 4),
        }
    
    def full_vulnerability_report(self, top_n: int = 20) -> List[dict]:
        """
        Run ablation on top-N nodes by centrality and return ranked vulnerability list.
        """
        # Ensure centrality is calculated
        scores = {node_id: self.G.nodes[node_id].get('betweenness_centrality', 0.0) for node_id in self.G.nodes()}
        sorted_nodes = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        
        report = []
        for node_id, bc in sorted_nodes[:top_n]:
            res = self.ablate_node(node_id)
            res["betweenness"] = round(float(bc), 6)
            report.append(res)
            
        return report
