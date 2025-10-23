#!/usr/bin/env python3
"""
Performance and Load Testing Suite
Measures throughput, response times, and identifies performance baselines
"""

import requests
import time
import statistics
import json
import threading
from datetime import datetime
from typing import List, Dict

API_BASE_URL = "http://localhost:8001"
RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "performance_tests": {},
    "load_tests": {}
}

class PerformanceTester:
    """Measure API performance metrics"""
    
    def __init__(self, url: str):
        self.url = url
        self.results = {}
    
    def measure_endpoint(self, endpoint: str, iterations: int = 100):
        """Measure response time for endpoint"""
        times = []
        errors = 0
        
        print(f"\n📊 Testing {endpoint} ({iterations} iterations)...")
        
        for i in range(iterations):
            try:
                start = time.time()
                response = requests.get(f"{self.url}{endpoint}", timeout=5)
                elapsed = (time.time() - start) * 1000  # ms
                
                if response.status_code == 200:
                    times.append(elapsed)
                else:
                    errors += 1
            except Exception as e:
                errors += 1
        
        if times:
            metrics = {
                "endpoint": endpoint,
                "iterations": iterations,
                "successes": len(times),
                "errors": errors,
                "min_ms": min(times),
                "max_ms": max(times),
                "mean_ms": statistics.mean(times),
                "median_ms": statistics.median(times),
                "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
                "p95_ms": sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0],
                "p99_ms": sorted(times)[int(len(times) * 0.99)] if len(times) > 1 else times[0],
            }
            
            print(f"  Min:    {metrics['min_ms']:.2f}ms")
            print(f"  Max:    {metrics['max_ms']:.2f}ms")
            print(f"  Mean:   {metrics['mean_ms']:.2f}ms")
            print(f"  Median: {metrics['median_ms']:.2f}ms")
            print(f"  P95:    {metrics['p95_ms']:.2f}ms")
            print(f"  P99:    {metrics['p99_ms']:.2f}ms")
            print(f"  Errors: {errors}")
            
            return metrics
        else:
            print(f"  ✗ All requests failed!")
            return None

class LoadTester:
    """Simulate concurrent user load"""
    
    def __init__(self, url: str):
        self.url = url
        self.results = []
        self.lock = threading.Lock()
    
    def worker(self, endpoint: str, user_id: int, duration: int):
        """Worker thread that makes requests"""
        start_time = time.time()
        request_count = 0
        error_count = 0
        times = []
        
        while time.time() - start_time < duration:
            try:
                req_start = time.time()
                response = requests.get(f"{self.url}{endpoint}", timeout=5)
                req_time = (time.time() - req_start) * 1000
                
                if response.status_code == 200:
                    times.append(req_time)
                    request_count += 1
                else:
                    error_count += 1
            except Exception:
                error_count += 1
        
        with self.lock:
            self.results.append({
                "user_id": user_id,
                "requests": request_count,
                "errors": error_count,
                "response_times": times
            })
    
    def simulate_concurrent_users(self, endpoint: str, num_users: int, duration: int = 10):
        """Simulate concurrent users"""
        print(f"\n⚡ Simulating {num_users} concurrent users for {duration}s...")
        
        threads = []
        self.results = []
        
        # Start worker threads
        start = time.time()
        for i in range(num_users):
            t = threading.Thread(target=self.worker, args=(endpoint, i, duration))
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        total_time = time.time() - start
        
        # Aggregate results
        total_requests = sum(r["requests"] for r in self.results)
        total_errors = sum(r["errors"] for r in self.results)
        all_times = []
        for r in self.results:
            all_times.extend(r["response_times"])
        
        metrics = {
            "num_users": num_users,
            "duration_sec": duration,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "requests_per_second": total_requests / total_time if total_time > 0 else 0,
            "avg_response_time_ms": statistics.mean(all_times) if all_times else 0,
            "success_rate": (total_requests / (total_requests + total_errors) * 100) if (total_requests + total_errors) > 0 else 0
        }
        
        print(f"  Requests:       {total_requests}")
        print(f"  Errors:         {total_errors}")
        print(f"  RPS:            {metrics['requests_per_second']:.2f}")
        print(f"  Avg Response:   {metrics['avg_response_time_ms']:.2f}ms")
        print(f"  Success Rate:   {metrics['success_rate']:.1f}%")
        
        return metrics

def main():
    """Run performance and load tests"""
    print("=" * 60)
    print("PERFORMANCE & LOAD TESTING")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Start Time: {RESULTS['timestamp']}\n")
    
    # Performance testing
    print("\n" + "=" * 60)
    print("PHASE 1: PERFORMANCE BASELINE")
    print("=" * 60)
    
    perf = PerformanceTester(API_BASE_URL)
    
    endpoints = [
        "/health",
        "/api/health",
        "/api/jobs",
        "/metrics"
    ]
    
    for endpoint in endpoints:
        result = perf.measure_endpoint(endpoint, iterations=100)
        if result:
            RESULTS["performance_tests"][endpoint] = result
    
    # Load testing - incremental concurrent users
    print("\n" + "=" * 60)
    print("PHASE 2: LOAD TESTING")
    print("=" * 60)
    
    loader = LoadTester(API_BASE_URL)
    
    load_scenarios = [
        (10, 10),   # 10 users for 10 seconds
        (25, 10),   # 25 users for 10 seconds
        (50, 10),   # 50 users for 10 seconds
    ]
    
    for num_users, duration in load_scenarios:
        result = loader.simulate_concurrent_users("/api/jobs", num_users, duration)
        key = f"{num_users}_users_{duration}s"
        RESULTS["load_tests"][key] = result
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    # Performance targets
    print("\n✓ Performance Baseline:")
    for endpoint, metrics in RESULTS["performance_tests"].items():
        mean = metrics["mean_ms"]
        target = 100 if "health" in endpoint else 200 if "jobs" in endpoint else 500
        status = "✓" if mean < target else "⚠"
        print(f"  {status} {endpoint:15} Mean: {mean:8.2f}ms (Target: <{target}ms)")
    
    # Load test summary
    print("\n✓ Load Test Results:")
    for scenario, metrics in RESULTS["load_tests"].items():
        rps = metrics["requests_per_second"]
        print(f"  {scenario:20} RPS: {rps:6.2f}, Success: {metrics['success_rate']:.1f}%")
    
    # Save results
    with open("PERFORMANCE_RESULTS.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    
    print(f"\n✓ Results saved to PERFORMANCE_RESULTS.json")
    
    print("\n" + "=" * 60)
    print("BASELINE METRICS ESTABLISHED")
    print("=" * 60)

if __name__ == "__main__":
    main()
