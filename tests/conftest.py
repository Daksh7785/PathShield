"""
Shared PyTest fixtures for Route Resilience unit and integration tests.
"""
import pytest
import numpy as np
import networkx as nx

from analysis.stress_test import StressTestEngine


@pytest.fixture
def synthetic_mask() -> np.ndarray:
    """Create a 256x256 binary mask representing vertical & horizontal roads (10px wide)."""
    mask = np.zeros((256, 256), dtype=np.uint8)
    mask[120:136, :] = 255  # Horizontal highway
    mask[:, 120:136] = 255  # Vertical highway
    return mask


@pytest.fixture
def synthetic_graph() -> nx.Graph:
    """Create a 10x10 grid graph with coordinates and default weights."""
    G = nx.grid_2d_graph(10, 10)
    G = nx.convert_node_labels_to_integers(G)
    
    # Assign attributes
    for u, v in G.edges():
        G[u][v]['weight'] = 1.0
        G[u][v]['length_meters'] = 1.0
        G[u][v]['is_healing_edge'] = False
        G[u][v]['confidence'] = 1.0
        
    for n in G.nodes():
        G.nodes[n]['longitude'] = float(n * 0.001 + 77.45)
        G.nodes[n]['latitude'] = float(n * 0.001 + 12.85)
        G.nodes[n]['pos'] = (float(n * 0.001 + 77.45), float(n * 0.001 + 12.85))
        G.nodes[n]['betweenness_centrality'] = 0.0
        G.nodes[n]['closeness_centrality'] = 0.0
        G.nodes[n]['degree'] = G.degree(n)
        G.nodes[n]['node_type'] = "intersection"
        G.nodes[n]['is_gateway'] = False
        G.nodes[n]['city_id'] = "test"
        
    return G


@pytest.fixture
def stress_engine(synthetic_graph) -> StressTestEngine:
    """Get StressTestEngine instance initialized with synthetic_graph."""
    return StressTestEngine(synthetic_graph)


# Mock database dependency for API testing
from api.main import app
from database.connection import get_db

async def mock_get_db():
    class MockResult:
        def scalars(self):
            class MockScalars:
                def all(self):
                    return []
                def first(self):
                    return None
            return MockScalars()
    class MockSession:
        async def execute(self, *args, **kwargs):
            return MockResult()
        async def commit(self):
            pass
        async def rollback(self):
            pass
        async def close(self):
            pass
    yield MockSession()

app.dependency_overrides[get_db] = mock_get_db

