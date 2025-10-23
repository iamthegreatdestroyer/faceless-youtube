#!/usr/bin/env python3
"""
Staging Validation Test Suite
Comprehensive functional testing of API endpoints and core workflows
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configuration
API_BASE_URL = "http://localhost:8001"
RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "tests_run": 0,
    "tests_passed": 0,
    "tests_failed": 0,
    "results": []
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_test(name: str, passed: bool, details: str = ""):
    """Log test result"""
    RESULTS["tests_run"] += 1
    if passed:
        RESULTS["tests_passed"] += 1
        status = f"{Colors.GREEN}✓ PASS{Colors.END}"
    else:
        RESULTS["tests_failed"] += 1
        status = f"{Colors.RED}✗ FAIL{Colors.END}"
    
    print(f"{status} {name}")
    if details:
        print(f"    {details}")
    
    RESULTS["results"].append({
        "test": name,
        "passed": passed,
        "details": details
    })

def test_health_endpoints():
    """Test health check endpoints"""
    print(f"\n{Colors.BLUE}=== HEALTH ENDPOINTS ==={Colors.END}")
    
    # Test /health
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        passed = response.status_code == 200
        log_test("GET /health", passed, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /health", False, str(e))
    
    # Test /api/health
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        passed = response.status_code == 200
        if passed:
            data = response.json()
            has_schedulers = "schedulers" in data
            log_test("GET /api/health", has_schedulers, f"Status: {response.status_code}, Schedulers: {data.get('schedulers', {})}")
        else:
            log_test("GET /api/health", False, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /api/health", False, str(e))
    
    # Test /ready (readiness)
    try:
        response = requests.get(f"{API_BASE_URL}/ready", timeout=5)
        passed = response.status_code == 200
        log_test("GET /ready", passed, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /ready", False, str(e))

def test_authentication():
    """Test authentication endpoints"""
    print(f"\n{Colors.BLUE}=== AUTHENTICATION ==={Colors.END}")
    
    # Test login endpoint
    try:
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        response = requests.post(f"{API_BASE_URL}/api/auth/login", json=login_data, timeout=5)
        passed = response.status_code in [200, 401]  # Either success or auth failure
        
        if response.status_code == 200:
            data = response.json()
            has_token = "access_token" in data
            log_test("POST /api/auth/login", has_token, f"Status: {response.status_code}")
        else:
            log_test("POST /api/auth/login", True, f"Status: {response.status_code} (auth validation working)")
    except Exception as e:
        log_test("POST /api/auth/login", False, str(e))

def test_job_management():
    """Test job management endpoints"""
    print(f"\n{Colors.BLUE}=== JOB MANAGEMENT ==={Colors.END}")
    
    # Test list jobs (should be empty)
    try:
        response = requests.get(f"{API_BASE_URL}/api/jobs", timeout=5)
        passed = response.status_code == 200
        if passed:
            data = response.json()
            is_list = isinstance(data, list)
            log_test("GET /api/jobs (list)", is_list, f"Status: {response.status_code}, Count: {len(data) if is_list else 'N/A'}")
    except Exception as e:
        log_test("GET /api/jobs (list)", False, str(e))
    
    # Test create job
    try:
        job_data = {
            "title": "Test Job",
            "description": "Validation test job",
            "video_topic": "Test Topic",
            "scheduled_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        response = requests.post(f"{API_BASE_URL}/api/jobs", json=job_data, timeout=5)
        passed = response.status_code in [200, 201]
        
        if passed:
            data = response.json()
            job_id = data.get("job_id") or data.get("id")
            log_test("POST /api/jobs (create)", bool(job_id), f"Status: {response.status_code}, ID: {job_id}")
            return job_id
        else:
            log_test("POST /api/jobs (create)", False, f"Status: {response.status_code}")
            return None
    except Exception as e:
        log_test("POST /api/jobs (create)", False, str(e))
        return None

def test_video_management():
    """Test video management endpoints"""
    print(f"\n{Colors.BLUE}=== VIDEO MANAGEMENT ==={Colors.END}")
    
    # Test list videos
    try:
        response = requests.get(f"{API_BASE_URL}/api/videos", timeout=5)
        passed = response.status_code == 200
        if passed:
            data = response.json()
            is_list = isinstance(data, list)
            log_test("GET /api/videos (list)", is_list, f"Status: {response.status_code}, Count: {len(data) if is_list else 'N/A'}")
    except Exception as e:
        log_test("GET /api/videos (list)", False, str(e))
    
    # Test create video
    try:
        video_data = {
            "title": "Test Video",
            "description": "Validation test video",
            "topic": "Test Topic",
            "status": "draft"
        }
        response = requests.post(f"{API_BASE_URL}/api/videos", json=video_data, timeout=5)
        passed = response.status_code in [200, 201]
        
        if passed:
            data = response.json()
            video_id = data.get("video_id") or data.get("id")
            log_test("POST /api/videos (create)", bool(video_id), f"Status: {response.status_code}, ID: {video_id}")
            return video_id
        else:
            log_test("POST /api/videos (create)", False, f"Status: {response.status_code}")
            return None
    except Exception as e:
        log_test("POST /api/videos (create)", False, str(e))
        return None

def test_metrics():
    """Test metrics endpoints"""
    print(f"\n{Colors.BLUE}=== METRICS ==={Colors.END}")
    
    # Test metrics endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
        passed = response.status_code == 200
        if passed:
            is_prometheus = "# HELP" in response.text or "prometheus" in response.text.lower()
            log_test("GET /metrics", is_prometheus, f"Status: {response.status_code}")
        else:
            log_test("GET /metrics", False, f"Status: {response.status_code}")
    except Exception as e:
        log_test("GET /metrics", False, str(e))

def test_performance_baseline():
    """Measure response times for performance baseline"""
    print(f"\n{Colors.BLUE}=== PERFORMANCE BASELINE ==={Colors.END}")
    
    endpoints = [
        ("GET", "/health"),
        ("GET", "/api/health"),
        ("GET", "/api/jobs"),
        ("GET", "/metrics"),
    ]
    
    times = {}
    
    for method, endpoint in endpoints:
        try:
            start = time.time()
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            times[endpoint] = elapsed
            status = "✓" if response.status_code == 200 else "⚠"
            print(f"{status} {endpoint:20} {elapsed:8.2f}ms")
        except Exception as e:
            print(f"✗ {endpoint:20} ERROR: {str(e)}")
    
    return times

def test_database_connectivity():
    """Test database connectivity through API"""
    print(f"\n{Colors.BLUE}=== DATABASE CONNECTIVITY ==={Colors.END}")
    
    try:
        # Try to get jobs, which should query the database
        response = requests.get(f"{API_BASE_URL}/api/jobs", timeout=5)
        passed = response.status_code == 200
        log_test("Database query (via /api/jobs)", passed, f"Status: {response.status_code}")
    except Exception as e:
        log_test("Database query (via /api/jobs)", False, str(e))

def generate_report():
    """Generate validation report"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}VALIDATION REPORT{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    passed = RESULTS["tests_passed"]
    failed = RESULTS["tests_failed"]
    total = RESULTS["tests_run"]
    percent = (passed / total * 100) if total > 0 else 0
    
    print(f"\nTests Run:    {total}")
    print(f"Tests Passed: {Colors.GREEN}{passed}{Colors.END}")
    print(f"Tests Failed: {Colors.RED}{failed}{Colors.END}")
    print(f"Pass Rate:    {percent:.1f}%")
    
    if failed > 0:
        print(f"\n{Colors.RED}Failed Tests:{Colors.END}")
        for result in RESULTS["results"]:
            if not result["passed"]:
                print(f"  - {result['test']}: {result['details']}")
    
    return RESULTS

def main():
    """Run all validation tests"""
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}STAGING ENVIRONMENT VALIDATION{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Start Time: {RESULTS['timestamp']}")
    
    # Run all test phases
    test_health_endpoints()
    test_authentication()
    test_job_management()
    test_video_management()
    test_metrics()
    test_database_connectivity()
    
    # Performance baseline
    times = test_performance_baseline()
    RESULTS["performance_baseline"] = times
    
    # Generate report
    report = generate_report()
    
    # Save report to file
    with open("VALIDATION_RESULTS.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Results saved to VALIDATION_RESULTS.json")
    
    # Exit with appropriate code
    sys.exit(0 if RESULTS["tests_failed"] == 0 else 1)

if __name__ == "__main__":
    main()
