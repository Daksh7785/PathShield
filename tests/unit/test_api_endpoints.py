"""
Unit tests for FastAPI endpoint routers.
"""
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_returns_200():
    """Verify that the health check endpoint returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "1.0.0"}


def test_cities_list_returns_array():
    """Verify that the cities endpoint returns a valid response format."""
    response = client.get("/api/v1/cities/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_stress_test_invalid_city_returns_404():
    """Verify that stress-testing an unregistered city ID returns a 404 error."""
    payload = {
        "scenario_type": "flood",
        "flood_bounds": [77.55, 12.90, 77.65, 13.00]
    }
    response = client.post("/api/v1/analysis/invalid_city_id/stress-test", json=payload)
    assert response.status_code == 404
