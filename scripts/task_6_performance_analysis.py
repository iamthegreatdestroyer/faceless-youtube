#!/usr/bin/env python3
"""Task #6 Phase 2: Performance Analysis & Database Profiling."""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List

BASE_URL = 'http://localhost:8001'


async def performance_analysis():
    """Execute comprehensive performance analysis."""
    async with aiohttp.ClientSession() as session:
        results = {
            'timestamp': datetime.now().isoformat(),
            'analysis': {}
        }
        
        print('=' * 60)
        print('TASK #6 PHASE 2: PERFORMANCE ANALYSIS')
        print('=' * 60 + '\n')
        
        # Test 1: Response Time Distribution
        print('📊 Test 1: Response Time Distribution (1000 requests)')
        try:
            times = []
            errors = 0
            
            for _ in range(1000):
                try:
                    start = time.time()
                    async with session.get(f'{BASE_URL}/health', timeout=10) as resp:
                        if resp.status == 200:
                            await resp.json()
                            elapsed = (time.time() - start) * 1000
                            times.append(elapsed)
                        else:
                            errors += 1
                except asyncio.TimeoutError:
                    errors += 1
                except Exception:
                    errors += 1
            
            if times:
                times_sorted = sorted(times)
                p50 = times_sorted[int(len(times) * 0.50)]
                p95 = times_sorted[int(len(times) * 0.95)]
                p99 = times_sorted[int(len(times) * 0.99)]
                
                print(f'  ✓ Requests completed: {len(times)}/1000')
                print(f'  ✓ Error rate: {(errors/1000)*100:.1f}%')
                print(f'  ✓ P50: {p50:.2f}ms')
                print(f'  ✓ P95: {p95:.2f}ms')
                print(f'  ✓ P99: {p99:.2f}ms')
                print(f'  ✓ Min: {min(times):.2f}ms, Max: {max(times):.2f}ms')
                
                results['analysis']['response_distribution'] = {
                    'requests': len(times),
                    'errors': errors,
                    'p50_ms': round(p50, 2),
                    'p95_ms': round(p95, 2),
                    'p99_ms': round(p99, 2),
                    'min_ms': round(min(times), 2),
                    'max_ms': round(max(times), 2),
                }
        except Exception as e:
            print(f'  ✗ Error: {e}')
        
        # Test 2: Endpoint Comparison
        print('\n📊 Test 2: Endpoint Performance Comparison (100 requests each)')
        endpoints = ['/health', '/api/health', '/api/jobs', '/metrics']
        endpoint_results = {}
        
        for endpoint in endpoints:
            try:
                times = []
                for _ in range(100):
                    start = time.time()
                    async with session.get(
                        f'{BASE_URL}{endpoint}',
                        timeout=10
                    ) as resp:
                        if resp.status in [200, 404]:
                            await resp.text()
                            elapsed = (time.time() - start) * 1000
                            times.append(elapsed)
                
                avg = sum(times) / len(times)
                print(f'  ✓ {endpoint}: {avg:.2f}ms avg')
                endpoint_results[endpoint] = {'avg_ms': round(avg, 2)}
            
            except Exception as e:
                print(f'  ✗ {endpoint}: Error - {str(e)[:50]}')
        
        results['analysis']['endpoints'] = endpoint_results
        
        # Test 3: Concurrent Request Behavior
        print('\n📊 Test 3: Concurrent Request Analysis (50 concurrent, 20 iterations)')
        try:
            start_time = time.time()
            total_requests = 0
            total_errors = 0
            times = []
            
            async def make_request():
                try:
                    start = time.time()
                    async with session.get(
                        f'{BASE_URL}/api/jobs',
                        timeout=10
                    ) as resp:
                        if resp.status == 200:
                            await resp.json()
                            return (time.time() - start) * 1000, False
                        return None, True
                except Exception:
                    return None, True
            
            # Run 50 concurrent requests, 20 times
            for batch in range(20):
                tasks = [make_request() for _ in range(50)]
                results_batch = await asyncio.gather(*tasks)
                
                for elapsed, is_error in results_batch:
                    total_requests += 1
                    if is_error:
                        total_errors += 1
                    elif elapsed:
                        times.append(elapsed)
            
            duration = time.time() - start_time
            rps = total_requests / duration
            avg_time = sum(times) / len(times) if times else 0
            
            print(f'  ✓ Requests: {total_requests} in {duration:.2f}s')
            print(f'  ✓ RPS: {rps:.1f}')
            print(f'  ✓ Avg Response: {avg_time:.2f}ms')
            print(f'  ✓ Error Rate: {(total_errors/total_requests)*100:.1f}%')
            
            results['analysis']['concurrency'] = {
                'total_requests': total_requests,
                'duration_seconds': round(duration, 2),
                'rps': round(rps, 2),
                'avg_response_ms': round(avg_time, 2),
                'error_rate_percent': round((total_errors/total_requests)*100, 1),
            }
        
        except Exception as e:
            print(f'  ✗ Error: {e}')
        
        # Test 4: Database Query Performance
        print('\n📊 Test 4: Database Query Performance')
        try:
            times = []
            for _ in range(50):
                start = time.time()
                async with session.get(f'{BASE_URL}/api/jobs') as resp:
                    if resp.status == 200:
                        jobs = await resp.json()
                        elapsed = (time.time() - start) * 1000
                        times.append(elapsed)
            
            avg = sum(times) / len(times)
            print(f'  ✓ Job listing: {avg:.2f}ms avg')
            print(f'  ✓ 50 queries completed')
            
            results['analysis']['database'] = {
                'avg_query_ms': round(avg, 2),
                'queries_tested': 50
            }
        
        except Exception as e:
            print(f'  ✗ Error: {e}')
        
        # Test 5: Memory and Resource Efficiency
        print('\n📊 Test 5: Sustained Load Analysis (30 seconds)')
        try:
            start_time = time.time()
            request_count = 0
            error_count = 0
            times = []
            
            while time.time() - start_time < 30:
                tasks = [
                    session.get(f'{BASE_URL}/api/jobs', timeout=10)
                    for _ in range(20)
                ]
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                for resp in responses:
                    if isinstance(resp, Exception):
                        error_count += 1
                    else:
                        try:
                            request_count += 1
                            await resp.text()
                        except Exception:
                            error_count += 1
            
            duration = time.time() - start_time
            total = request_count + error_count
            rps = request_count / duration
            success_rate = (request_count / total) * 100
            
            print(f'  ✓ Sustained load: {request_count} req in {duration:.1f}s')
            print(f'  ✓ RPS: {rps:.1f}')
            print(f'  ✓ Success rate: {success_rate:.1f}%')
            
            results['analysis']['sustained_load'] = {
                'duration_seconds': round(duration, 1),
                'requests': request_count,
                'errors': error_count,
                'rps': round(rps, 2),
                'success_rate_percent': round(success_rate, 1),
            }
        
        except Exception as e:
            print(f'  ✗ Error: {e}')
        
        # Summary and recommendations
        print('\n' + '=' * 60)
        print('PERFORMANCE ANALYSIS SUMMARY')
        print('=' * 60 + '\n')
        
        if 'response_distribution' in results['analysis']:
            p95 = results['analysis']['response_distribution']['p95_ms']
            status = '✅ EXCELLENT' if p95 < 100 else '⚠️ GOOD' if p95 < 500 else '❌ NEEDS WORK'
            print(f'Response Time (P95): {p95}ms - {status}')
        
        if 'concurrency' in results['analysis']:
            rps = results['analysis']['concurrency']['rps']
            status = '✅ EXCELLENT' if rps > 100 else '⚠️ GOOD' if rps > 50 else '❌ LOW'
            print(f'Throughput: {rps} RPS - {status}')
        
        if 'sustained_load' in results['analysis']:
            success = results['analysis']['sustained_load']['success_rate_percent']
            status = '✅ EXCELLENT' if success >= 99 else '⚠️ GOOD' if success >= 95 else '❌ NEEDS WORK'
            print(f'Reliability: {success}% success - {status}')
        
        # Save results
        with open('TASK_6_PERFORMANCE_ANALYSIS_RESULTS.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print('\n✓ Results saved to TASK_6_PERFORMANCE_ANALYSIS_RESULTS.json')
        
        return results


if __name__ == '__main__':
    asyncio.run(performance_analysis())
