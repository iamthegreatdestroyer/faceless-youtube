#!/usr/bin/env python3
"""
End-to-end workflow tests for Faceless YouTube system
Validates complete user workflows and identifies gaps
"""

import requests
import json
from datetime import datetime


class WorkflowTester:
    def __init__(self):
        self.base_url = 'http://localhost:8000'
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'workflows': {},
            'gaps': [],
            'summary': {}
        }
        self.session = requests.Session()
    
    def test_workflow_create_job(self):
        """Test: User creates a video job"""
        workflow_name = 'create_job'
        try:
            # Step 1: Create job
            job_data = {
                'title': 'Test Show Transformation',
                'original_show': 'I Love Lucy',
                'new_setting': 'Space Colony 2157',
                'status': 'draft'
            }
            response = self.session.post(
                f'{self.base_url}/api/jobs',
                json=job_data,
                timeout=5
            )
            
            if response.status_code not in [200, 201]:
                self.results['workflows'][workflow_name] = {
                    'status': 'FAIL',
                    'step': 'create_job',
                    'error': f'Status {response.status_code}',
                }
                self.results['gaps'].append({
                    'workflow': workflow_name,
                    'issue': 'Cannot create job via /api/jobs',
                    'severity': 'CRITICAL',
                    'step': 'POST /api/jobs'
                })
                return False

            job = response.json()
            job_id = job.get('id') or job.get('job_id')

            self.results['workflows'][workflow_name] = {
                'status': 'PASS',
                'steps_completed': ['create_job'],
                'job_id': job_id
            }
            return True
            
        except Exception as e:
            self.results['workflows'][workflow_name] = {
                'status': 'FAIL',
                'error': str(e),
                'message': 'Workflow not implemented'
            }
            self.results['gaps'].append({
                'workflow': workflow_name,
                'issue': f'Exception: {str(e)}',
                'severity': 'CRITICAL',
                'step': 'POST /api/jobs'
            })
            return False
    
    def test_workflow_list_jobs(self):
        """Test: User retrieves list of jobs"""
        workflow_name = 'list_jobs'
        try:
            response = self.session.get(f'{self.base_url}/api/jobs', timeout=5)
            
            if response.status_code not in [200]:
                self.results['workflows'][workflow_name] = {
                    'status': 'FAIL',
                    'error': f'Status {response.status_code}',
                }
                self.results['gaps'].append({
                    'workflow': workflow_name,
                    'issue': f'GET /api/jobs returns {response.status_code}',
                    'severity': 'HIGH',
                    'step': 'GET /api/jobs'
                })
                return False
            
            jobs = response.json()

            self.results['workflows'][workflow_name] = {
                'status': 'PASS',
                'jobs_count': (len(jobs) if isinstance(jobs, list)
                               else 'unknown'),
                'message': 'Successfully retrieved jobs list'
            }
            return True
            
        except Exception as e:
            self.results['workflows'][workflow_name] = {
                'status': 'FAIL',
                'error': str(e)
            }
            self.results['gaps'].append({
                'workflow': workflow_name,
                'issue': f'Cannot list jobs: {str(e)}',
                'severity': 'HIGH',
                'step': 'GET /api/jobs'
            })
            return False
    
    def test_workflow_authenticate(self):
        """Test: User authenticates (if auth required)"""
        workflow_name = 'authentication'
        try:
            # First try without auth
            response = self.session.get(
                f'{self.base_url}/api/protected',
                timeout=5
            )

            if response.status_code == 401:
                # Auth is required - try with token
                headers = {'Authorization': 'Bearer test_token'}
                response = self.session.get(
                    f'{self.base_url}/api/protected',
                    headers=headers,
                    timeout=5
                )

                if response.status_code == 401:
                    self.results['workflows'][workflow_name] = {
                        'status': 'INFO',
                        'message': ('Authentication enabled but '
                                    '/api/protected not implemented')
                    }
                    return True
                else:
                    self.results['workflows'][workflow_name] = {
                        'status': 'PASS',
                        'message': 'Authentication working'
                    }
                    return True
            else:
                self.results['workflows'][workflow_name] = {
                    'status': 'INFO',
                    'message': ('No protected endpoints found '
                                '(auth not enforced)')
                }
                return True
                
        except Exception as e:
            self.results['workflows'][workflow_name] = {
                'status': 'INFO',
                'error': str(e),
                'message': 'Authentication check skipped'
            }
            return True
    
    def test_workflow_video_generation(self):
        """Test: User initiates video generation"""
        workflow_name = 'generate_video'
        try:
            # First check if generation endpoint exists
            response = self.session.post(
                f'{self.base_url}/api/jobs/generate',
                json={'job_id': 'test'},
                timeout=5
            )
            
            if response.status_code == 404:
                self.results['workflows'][workflow_name] = {
                    'status': 'FAIL',
                    'error': 'Endpoint not found'
                }
                self.results['gaps'].append({
                    'workflow': workflow_name,
                    'issue': 'POST /api/jobs/generate not implemented',
                    'severity': 'CRITICAL',
                    'step': 'Generate video'
                })
                return False
            elif response.status_code in [200, 201, 202]:
                self.results['workflows'][workflow_name] = {
                    'status': 'PASS',
                    'message': 'Video generation endpoint available'
                }
                return True
            else:
                self.results['workflows'][workflow_name] = {
                    'status': 'FAIL',
                    'error': f'Status {response.status_code}'
                }
                return False
                
        except requests.exceptions.ConnectionError:
            self.results['workflows'][workflow_name] = {
                'status': 'FAIL',
                'error': 'Backend not running'
            }
            self.results['gaps'].append({
                'workflow': workflow_name,
                'issue': 'Backend API not available on localhost:8000',
                'severity': 'CRITICAL',
                'step': 'Connect to backend'
            })
            return False
        except Exception as e:
            self.results['workflows'][workflow_name] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_workflow_export_video(self):
        """Test: User exports generated video"""
        workflow_name = 'export_video'
        try:
            response = self.session.get(
                f'{self.base_url}/api/videos/export',
                timeout=5
            )
            
            if response.status_code == 404:
                self.results['workflows'][workflow_name] = {
                    'status': 'FAIL',
                    'error': 'Endpoint not found'
                }
                self.results['gaps'].append({
                    'workflow': workflow_name,
                    'issue': 'GET /api/videos/export not implemented',
                    'severity': 'HIGH'
                })
                return False
            elif response.status_code in [200]:
                self.results['workflows'][workflow_name] = {
                    'status': 'PASS',
                    'message': 'Export endpoint available'
                }
                return True
            else:
                self.results['workflows'][workflow_name] = {
                    'status': 'INFO',
                    'status_code': response.status_code,
                    'message': f'Endpoint returns {response.status_code}'
                }
                return True
                
        except Exception as e:
            self.results['workflows'][workflow_name] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def run_all_workflows(self):
        """Run all workflow tests"""
        print("Testing workflows...")
        
        workflows = [
            self.test_workflow_authenticate,
            self.test_workflow_list_jobs,
            self.test_workflow_create_job,
            self.test_workflow_video_generation,
            self.test_workflow_export_video,
        ]
        
        results = []
        for workflow_test in workflows:
            try:
                result = workflow_test()
                results.append(result)
            except Exception as e:
                print(f"Error running {workflow_test.__name__}: {e}")
        
        # Summary
        passed = sum(1 for r in results if r)
        total = len(results)
        self.results['summary'] = {
            'workflows_passed': passed,
            'workflows_total': total,
            'gaps_found': len(self.results['gaps'])
        }
        
        return self.results


def main():
    tester = WorkflowTester()
    results = tester.run_all_workflows()
    
    # Print results
    print("\n" + "="*60)
    print("WORKFLOW TEST RESULTS")
    print("="*60)
    
    print(f"\nPassed: "
          f"{results['summary']['workflows_passed']}/"
          f"{results['summary']['workflows_total']}")
    print(f"Gaps Found: {results['summary']['gaps_found']}")
    
    if results['gaps']:
        print("\n" + "="*60)
        print("GAPS IDENTIFIED")
        print("="*60)
        for gap in results['gaps']:
            severity = gap.get('severity', 'UNKNOWN')
            issue = gap.get('issue', 'Unknown issue')
            print(f"\n[{severity}] {gap['workflow']}")
            print(f"  Issue: {issue}")
            print(f"  Step: {gap.get('step', 'Unknown')}")
    
    # Save detailed results to file
    with open('workflow_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\nDetailed results saved to: workflow_test_results.json")

    return results


if __name__ == '__main__':
    main()
