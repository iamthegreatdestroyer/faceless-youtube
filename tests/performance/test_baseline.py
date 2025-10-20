"""
Performance baseline tests for staging environment.
Establishes metrics for regression detection.
"""

import pytest
import time
import statistics


class TestAPIPerformance:
    @pytest.fixture
    def client(self):
        import httpx
        return httpx.Client(base_url="http://api-staging:8000", timeout=30)

    def measure_endpoint(self, client, endpoint: str, runs: int = 10) -> dict:
        times = []
        for _ in range(runs):
            start = time.time()
            response = client.get(endpoint)
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "min": min(times),
            "max": max(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        }

    def test_list_jobs_performance(self, client):
        metrics = self.measure_endpoint(client, "/api/jobs")
        assert metrics["mean"] < 0.5, f"List jobs avg: {metrics['mean']:.3f}s (target: <0.5s)"

    def test_get_statistics_performance(self, client):
        metrics = self.measure_endpoint(client, "/api/statistics")
        assert metrics["mean"] < 1.0, f"Stats avg: {metrics['mean']:.3f}s (target: <1.0s)"

    def test_health_check_performance(self, client):
        metrics = self.measure_endpoint(client, "/health", runs=20)
        assert metrics["mean"] < 0.1, f"Health check avg: {metrics['mean']:.3f}s (target: <0.1s)"


class TestDatabasePerformance:
    @pytest.mark.asyncio
    async def test_query_performance_postgresql(self):
        from src.database.postgres import get_db
        import time
        async with get_db() as db:
            start = time.time()
            result = await db.execute("SELECT COUNT(*) FROM jobs")
            elapsed = time.time() - start
            # Allow slightly higher latency in containerized test environments
            assert elapsed < 0.2, f"Query time: {elapsed:.3f}s (target: <0.2s)"

    @pytest.mark.asyncio
    async def test_query_performance_mongodb(self):
        from src.database.mongodb import get_mongo
        import time
        mongo = get_mongo()
        start = time.time()
        result = await mongo.faceless_youtube_staging.jobs.count_documents({})
        elapsed = time.time() - start
        assert elapsed < 0.2, f"Query time: {elapsed:.3f}s (target: <0.2s)"
