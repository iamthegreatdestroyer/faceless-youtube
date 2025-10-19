"""
Smoke tests for staging environment.
Validates core functionality works end-to-end.
"""

import pytest
import httpx
from datetime import datetime

BASE_URL = "http://api-staging:8000"
TIMEOUT = 30.0


class TestAPIEndpoints:
    """Test all major API endpoints respond correctly."""

    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=TIMEOUT)

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_list_jobs(self, client):
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_job(self, client):
        job_data = {
            "script": "Test video about AI",
            "scheduled_at": datetime.now().isoformat(),
            "video_type": "educational",
        }
        response = client.post("/api/jobs", json=job_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "job_id" in data or "id" in data

    def test_calendar_endpoint(self, client):
        response = client.get("/api/calendar")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_statistics_endpoint(self, client):
        response = client.get("/api/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data or "stats" in data


class TestDashboardAccess:
    """Test dashboard is accessible."""

    @pytest.fixture
    def client(self):
        return httpx.Client(timeout=TIMEOUT)

    def test_dashboard_loads(self, client):
        response = client.get("http://dashboard-staging:3000")
        assert response.status_code == 200
        assert "<!DOCTYPE" in response.text or "<html" in response.text


class TestDatabaseConnectivity:
    """Test database connections."""

    @pytest.mark.asyncio
    async def test_postgresql_connected(self):
        from src.database.postgres import get_db
        async with get_db() as db:
            result = await db.execute("SELECT 1")
            assert result is not None

    @pytest.mark.asyncio
    async def test_mongodb_connected(self):
        from src.database.mongodb import get_mongo
        mongo = get_mongo()
        result = await mongo.admin.command('ping')
        assert result.get('ok') == 1


class TestConfiguration:
    def test_environment_is_staging(self):
        import os
        assert os.getenv("ENVIRONMENT") == "staging"

    def test_required_env_vars_present(self):
        import os
        required_vars = ["DATABASE_URL", "MONGODB_URI", "REDIS_URL"]
        for var in required_vars:
            assert os.getenv(var) is not None, f"Missing {var}"
