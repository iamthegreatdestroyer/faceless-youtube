#!/usr/bin/env python3
"""
Health check for Faceless YouTube system
Validates all major components are operational
"""

import requests
import asyncio
import json
from datetime import datetime


class HealthChecker:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'overall_status': 'UNKNOWN'
        }
    
    async def check_backend_api(self):
        """Check backend API availability"""
        try:
            response = requests.get('http://localhost:8000/docs', timeout=5)
            self.results['checks']['backend_api'] = {
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response_code': response.status_code,
                'message': 'Backend API responding'
            }
        except Exception as e:
            self.results['checks']['backend_api'] = {
                'status': 'FAIL',
                'error': str(e),
                'message': 'Backend API not responding'
            }
    
    async def check_frontend(self):
        """Check frontend availability"""
        try:
            response = requests.get('http://localhost:3000', timeout=5)
            self.results['checks']['frontend'] = {
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response_code': response.status_code,
                'message': 'Frontend responding'
            }
        except Exception as e:
            self.results['checks']['frontend'] = {
                'status': 'FAIL',
                'error': str(e),
                'message': 'Frontend not responding'
            }
    
    async def check_health_endpoint(self):
        """Check health endpoint specifically"""
        try:
            response = requests.get(
                'http://localhost:8000/api/health',
                timeout=5
            )
            status_ok = response.status_code == 200
            msg = ('Health endpoint responding' if status_ok
                   else 'Health endpoint not found')
            self.results['checks']['health_endpoint'] = {
                'status': 'PASS' if status_ok else 'FAIL',
                'response_code': response.status_code,
                'message': msg
            }
        except Exception as e:
            self.results['checks']['health_endpoint'] = {
                'status': 'FAIL',
                'error': str(e),
                'message': 'Health endpoint not responding'
            }
    
    async def check_api_endpoints(self):
        """Check major API endpoints"""
        endpoints = [
            '/api/jobs',
            '/api/videos',
            '/api/schedules',
            '/api/stats',
        ]
        
        endpoint_results = {}
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f'http://localhost:8000{endpoint}',
                    timeout=5
                )
                status_valid = response.status_code in [200, 404]
                endpoint_results[endpoint] = {
                    'status': 'PASS' if status_valid else 'FAIL',
                    'response_code': response.status_code,
                }
            except Exception as e:
                endpoint_results[endpoint] = {
                    'status': 'FAIL',
                    'error': str(e),
                }
        
        self.results['checks']['api_endpoints'] = endpoint_results
    
    async def run_all_checks(self):
        """Run all health checks"""
        await asyncio.gather(
            self.check_backend_api(),
            self.check_frontend(),
            self.check_health_endpoint(),
            self.check_api_endpoints()
        )
        
        # Determine overall status
        all_checks = []
        for check_name, check_result in self.results['checks'].items():
            if isinstance(check_result, dict) and 'status' in check_result:
                all_checks.append(check_result.get('status') == 'PASS')
            elif isinstance(check_result, dict):
                # For nested dicts like api_endpoints
                for sub_check in check_result.values():
                    if isinstance(sub_check, dict):
                        all_checks.append(sub_check.get('status') == 'PASS')
        
        self.results['overall_status'] = ('HEALTHY' if all(all_checks)
                                          else 'DEGRADED')
        
        return self.results


async def main():
    checker = HealthChecker()
    results = await checker.run_all_checks()
    print(json.dumps(results, indent=2))
    return results

if __name__ == '__main__':
    results = asyncio.run(main())
    
    # Print summary
    print("\n" + "="*60)
    print(f"Overall Status: {results['overall_status']}")
    print("="*60)
    
    # Print individual check results
    for check_name, check_result in results['checks'].items():
        if isinstance(check_result, dict) and 'status' in check_result:
            status = check_result.get('status')
            message = check_result.get('message', '')
            if status == 'PASS':
                print(f"✓ {check_name}: {status} - {message}")
            else:
                print(f"✗ {check_name}: {status}")
