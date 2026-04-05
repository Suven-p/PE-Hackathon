"""
Integration tests for GET /health.
"""
import pytest

pytestmark = pytest.mark.usefixtures("clean_tables")


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok_status(client):
    data = response = client.get("/health").get_json()
    assert data == {"status": "ok"}
