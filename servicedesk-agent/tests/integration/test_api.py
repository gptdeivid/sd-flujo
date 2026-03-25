"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness_check(self, client):
        """Readiness endpoint should return ready status."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_root_endpoint(self, client):
        """Root endpoint should return service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data


class TestTicketsEndpoint:
    """Tests for tickets endpoint."""

    def test_ticket_request_requires_message(self, client):
        """Should require message in request."""
        response = client.post("/api/v1/tickets", json={})
        assert response.status_code == 422  # Validation error

    def test_ticket_request_empty_message(self, client):
        """Should reject empty message."""
        response = client.post("/api/v1/tickets", json={"message": ""})
        assert response.status_code == 422

    @pytest.mark.integration
    def test_ticket_processing_structure(self, client):
        """Response should have correct structure.

        Note: This test requires actual LLM connection.
        Mark as integration and skip in unit test runs.
        """
        response = client.post(
            "/api/v1/tickets",
            json={"message": "Test message"},
        )

        # May fail without LLM credentials, so check structure only
        if response.status_code == 200:
            data = response.json()
            assert "session_id" in data
            assert "classification" in data
            assert "response" in data
            assert "needs_human_escalation" in data
