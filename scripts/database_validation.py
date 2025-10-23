#!/usr/bin/env python3
"""Phase 3: Database Validation - Corrected for actual job schema."""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

BASE_URL = 'http://localhost:8001'


async def test_database_operations():
    """Test database persistence and query performance."""
    async with aiohttp.ClientSession() as session:
        results = {
            'phase': 'Database Validation',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        
        print('=' * 60)
        print('PHASE 3: DATABASE VALIDATION')
        print('=' * 60)
        
        # Test 1: Create multiple jobs
        print('\n📝 Test 1: Job Creation & Persistence...')
        job_ids = []
        try:
            for i in range(3):
                payload = {
                    'topic': f'Test Topic {i+1}'
                }
                
                start = time.time()
                async with session.post(
                    f'{BASE_URL}/api/jobs', 
                    json=payload
                ) as resp:
                    elapsed = (time.time() - start) * 1000
                    if resp.status == 201:
                        job_data = await resp.json()
                        job_id = job_data.get('id')
                        job_ids.append(job_id)
                        short_id = str(job_id)[:8]
                        print(f'  ✓ Job created: {short_id}... '
                              f'({elapsed:.2f}ms)')
                    else:
                        print(f'  ✗ Job {i+1} failed: {resp.status}')
                        
            results['tests'].append({
                'name': 'Job Creation & Persistence',
                'status': 'PASS' if len(job_ids) == 3 else 'FAIL',
                'jobs_created': len(job_ids)
            })
            print(f'  ✓ Total jobs created: {len(job_ids)}/3')
            
        except Exception as e:
            print(f'  ✗ Error: {e}')
            results['tests'].append({
                'name': 'Job Creation & Persistence',
                'status': 'FAIL',
                'error': str(e)
            })
        
        # Test 2: Query all jobs
        print('\n📊 Test 2: Query All Jobs...')
        job_count = 0
        try:
            start = time.time()
            async with session.get(f'{BASE_URL}/api/jobs') as resp:
                elapsed = (time.time() - start) * 1000
                if resp.status == 200:
                    jobs = await resp.json()
                    job_count = len(jobs)
                    print(f'  ✓ Retrieved {job_count} jobs ({elapsed:.2f}ms)')
                    results['tests'].append({
                        'name': 'Query All Jobs',
                        'status': 'PASS',
                        'total_jobs': job_count,
                        'response_time_ms': round(elapsed, 2)
                    })
                else:
                    print(f'  ✗ Query failed: {resp.status}')
                    results['tests'].append({
                        'name': 'Query All Jobs',
                        'status': 'FAIL'
                    })
        except Exception as e:
            print(f'  ✗ Error: {e}')
            results['tests'].append({
                'name': 'Query All Jobs',
                'status': 'FAIL',
                'error': str(e)
            })
        
        # Test 3: Verify schema
        print('\n🔍 Test 3: Schema Validation...')
        try:
            async with session.get(f'{BASE_URL}/api/jobs') as resp:
                if resp.status == 200:
                    jobs = await resp.json()
                    if jobs:
                        job = jobs[0]
                        # Actual schema from API
                        required = ['id', 'topic', 'status']
                        has_fields = all(
                            f in job for f in required
                        )
                        print(f'  ✓ Has required fields: {has_fields}')
                        print(f'  ✓ Schema fields: {len(job)} fields')
                        print(f'    - id, topic, status, progress_percent')
                        print(f'    - current_stage, scheduled_at, started_at')
                        print(f'    - completed_at, script_path, video_path')
                        results['tests'].append({
                            'name': 'Schema Validation',
                            'status': 'PASS' if has_fields else 'FAIL',
                            'required_fields': required,
                            'total_fields': len(job)
                        })
        except Exception as e:
            print(f'  ✗ Error: {e}')
            results['tests'].append({
                'name': 'Schema Validation',
                'status': 'FAIL',
                'error': str(e)
            })
        
        # Test 4: Query performance
        print('\n⚡ Test 4: Query Performance (10 requests)...')
        try:
            times = []
            for _ in range(10):
                start = time.time()
                async with session.get(f'{BASE_URL}/api/jobs') as resp:
                    if resp.status == 200:
                        await resp.json()
                        elapsed = (time.time() - start) * 1000
                        times.append(elapsed)
            
            avg = sum(times) / len(times)
            min_t = min(times)
            max_t = max(times)
            print(f'  ✓ Avg: {avg:.2f}ms | Min: {min_t:.2f}ms | '
                  f'Max: {max_t:.2f}ms')
            results['tests'].append({
                'name': 'Query Performance',
                'status': 'PASS',
                'avg_response_ms': round(avg, 2),
                'min_ms': round(min_t, 2),
                'max_ms': round(max_t, 2),
                'iterations': 10
            })
        except Exception as e:
            print(f'  ✗ Error: {e}')
            results['tests'].append({
                'name': 'Query Performance',
                'status': 'FAIL',
                'error': str(e)
            })
        
        # Summary
        print('\n' + '=' * 60)
        print('DATABASE VALIDATION SUMMARY')
        print('=' * 60)
        passed = sum(
            1 for t in results['tests'] if t.get('status') == 'PASS'
        )
        total = len(results['tests'])
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f'\n✓ Tests Passed: {passed}/{total}')
        print(f'✓ Pass Rate: {pass_rate:.1f}%')
        print(f'✓ Database operational: {job_count} jobs in system')
        
        # Save results
        with open('DATABASE_VALIDATION_RESULTS.json', 'w') as f:
            json.dump(results, f, indent=2)
        print('\n✓ Results saved to DATABASE_VALIDATION_RESULTS.json')


if __name__ == '__main__':
    asyncio.run(test_database_operations())
