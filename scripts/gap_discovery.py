#!/usr/bin/env python3
"""
Comprehensive Gap Discovery for Faceless YouTube System
Identifies all gaps blocking production deployment
"""

import json
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class GapDiscovery:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'gaps': [],
            'warnings': [],
            'info': [],
            'summary': {}
        }

    def discover_missing_endpoints(self) -> List[Dict]:
        """Analyze API for missing critical endpoints"""
        gaps = []
        
        main_py = self.project_root / 'src' / 'api' / 'main.py'
        if not main_py.exists():
            gaps.append({
                'id': 'API_MISSING',
                'title': 'API main.py not found',
                'severity': 'CRITICAL',
                'file': str(main_py),
                'effort': 'HIGH',
                'description': 'Core API file missing, cannot start backend'
            })
            return gaps

        try:
            with open(main_py, 'r') as f:
                content = f.read()

            # Check for required endpoints
            required_endpoints = {
                '/health': 'Basic health check',
                '/api/health': 'API health endpoint',
                '/api/jobs': 'Job management',
                '/api/videos': 'Video management',
                '/api/generate': 'Video generation trigger'
            }

            for endpoint, description in required_endpoints.items():
                if endpoint not in content:
                    gaps.append({
                        'id': f'ENDPOINT_{endpoint.replace("/", "_").upper()}',
                        'title': f'Missing endpoint: {endpoint}',
                        'severity': 'HIGH' if 'jobs' in endpoint
                                    else 'MEDIUM',
                        'file': str(main_py),
                        'effort': 'MEDIUM',
                        'description': f'{description} endpoint not'
                                       ' implemented'
                    })

        except Exception as e:
            gaps.append({
                'id': 'API_PARSE_ERROR',
                'title': f'Error analyzing API: {str(e)}',
                'severity': 'MEDIUM',
                'file': str(main_py),
                'effort': 'MEDIUM'
            })

        return gaps

    def check_database_connectivity(self) -> List[Dict]:
        """Check if databases are configured and accessible"""
        gaps = []

        # Check for .env file
        env_file = self.project_root / '.env'
        if not env_file.exists():
            gaps.append({
                'id': 'ENV_MISSING',
                'title': 'Missing .env configuration file',
                'severity': 'CRITICAL',
                'file': '.env',
                'effort': 'LOW',
                'description': 'Environment variables not configured'
            })
        else:
            # Check for required DB variables
            with open(env_file, 'r') as f:
                env_content = f.read()

            required_vars = [
                'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER',
                'REDIS_HOST', 'MONGODB_URL'
            ]

            missing_vars = [var for var in required_vars
                            if var not in env_content]
            if missing_vars:
                gaps.append({
                    'id': 'ENV_VARS_MISSING',
                    'title': f'Missing environment variables: {missing_vars}',
                    'severity': 'MEDIUM',
                    'file': '.env',
                    'effort': 'LOW',
                    'description': 'Database connection not fully configured'
                })

        return gaps

    def check_test_coverage(self) -> List[Dict]:
        """Analyze test coverage and missing tests"""
        gaps = []

        tests_dir = self.project_root / 'tests'
        if not tests_dir.exists():
            gaps.append({
                'id': 'TESTS_DIR_MISSING',
                'title': 'Tests directory not found',
                'severity': 'HIGH',
                'file': str(tests_dir),
                'effort': 'HIGH',
                'description': 'No test infrastructure'
            })
            return gaps

        # Count test files
        test_files = list(tests_dir.rglob('test_*.py'))
        if len(test_files) < 5:
            gaps.append({
                'id': 'TESTS_SPARSE',
                'title': (f'Insufficient test coverage '
                          f'({len(test_files)} test files)'),
                'severity': 'MEDIUM',
                'file': str(tests_dir),
                'effort': 'HIGH',
                'description': 'Need more comprehensive test suite'
            })

        return gaps

    def check_docker_setup(self) -> List[Dict]:
        """Verify Docker configuration"""
        gaps = []

        docker_files = {
            'docker-compose.yml': 'Development stack',
            'docker-compose.staging.yml': 'Staging stack',
            'docker-compose.test.yml': 'Test stack',
            'Dockerfile.prod': 'Production build'
        }

        for filename, description in docker_files.items():
            path = self.project_root / filename
            if not path.exists():
                gaps.append({
                    'id': f'DOCKER_{filename.replace(".", "_").upper()}',
                    'title': f'Missing: {filename}',
                    'severity': 'MEDIUM',
                    'file': filename,
                    'effort': 'MEDIUM',
                    'description': f'{description} not configured'
                })

        return gaps

    def check_frontend_setup(self) -> List[Dict]:
        """Verify frontend configuration"""
        gaps = []

        dashboard_dir = self.project_root / 'dashboard'
        if not dashboard_dir.exists():
            gaps.append({
                'id': 'DASHBOARD_MISSING',
                'title': 'Dashboard/frontend not found',
                'severity': 'HIGH',
                'file': str(dashboard_dir),
                'effort': 'HIGH',
                'description': 'Frontend application not present'
            })
            return gaps

        # Check for package.json
        package_json = dashboard_dir / 'package.json'
        if not package_json.exists():
            gaps.append({
                'id': 'PACKAGE_JSON_MISSING',
                'title': 'Dashboard package.json not found',
                'severity': 'HIGH',
                'file': str(package_json),
                'effort': 'LOW',
                'description': 'Frontend dependencies not configured'
            })

        return gaps

    def check_critical_modules(self) -> List[Dict]:
        """Check if critical Python modules are importable"""
        gaps = []

        critical_modules = {
            'src.api.main': 'API application',
            'src.database.postgres': 'PostgreSQL integration',
            'src.models': 'Data models',
            'src.config': 'Configuration'
        }

        for module_name, description in critical_modules.items():
            try:
                spec = importlib.util.find_spec(module_name)
                if spec is None:
                    gaps.append({
                        'id': (f'MODULE_'
                               f'{module_name.replace(".", "_").upper()}'),
                        'title': f'Module not found: {module_name}',
                        'severity': 'HIGH',
                        'file': module_name.replace('.', '/') + '.py',
                        'effort': 'MEDIUM',
                        'description': f'{description} module missing'
                    })
            except (ImportError, ModuleNotFoundError):
                gaps.append({
                    'id': f'MODULE_{module_name.replace(".", "_").upper()}',
                    'title': f'Module import failed: {module_name}',
                    'severity': 'HIGH',
                    'file': module_name.replace('.', '/') + '.py',
                    'effort': 'MEDIUM',
                    'description': f'{description} not properly configured'
                })

        return gaps

    def check_deployment_readiness(self) -> List[Dict]:
        """Check deployment-specific requirements"""
        gaps = []

        # Check for deployment checklists/guides
        deployment_files = [
            'PRODUCTION_DEPLOYMENT_CHECKLIST.md',
            'STAGING_DEPLOYMENT_CHECKLIST.md',
            'DEPLOYMENT_GUIDE.md'
        ]

        docs_found = 0
        for doc in deployment_files:
            if (self.project_root / doc).exists():
                docs_found += 1

        if docs_found == 0:
            gaps.append({
                'id': 'DEPLOYMENT_DOCS_MISSING',
                'title': 'No deployment documentation found',
                'severity': 'MEDIUM',
                'file': 'root',
                'effort': 'LOW',
                'description': 'Deployment procedures not documented'
            })

        # Check for CI/CD
        ci_dir = self.project_root / '.github' / 'workflows'
        if not ci_dir.exists():
            gaps.append({
                'id': 'CI_CD_MISSING',
                'title': 'No CI/CD pipeline configured',
                'severity': 'MEDIUM',
                'file': str(ci_dir),
                'effort': 'MEDIUM',
                'description': 'GitHub Actions workflows not set up'
            })

        return gaps

    def check_security_configuration(self) -> List[Dict]:
        """Check security-related configurations"""
        gaps = []

        # Check for SECURITY.md
        if not (self.project_root / 'SECURITY.md').exists():
            gaps.append({
                'id': 'SECURITY_MD_MISSING',
                'title': 'Missing SECURITY.md file',
                'severity': 'LOW',
                'file': 'SECURITY.md',
                'effort': 'LOW',
                'description': 'Security policy not documented'
            })

        # Check for secrets management
        env_file = self.project_root / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_content = f.read()
                if any(keyword in env_content.lower()
                       for keyword in ['password=', 'secret=', 'key=']):
                    # This could be a security issue if actually secret values
                    self.results['warnings'].append({
                        'id': 'POTENTIAL_SECRETS_IN_ENV',
                        'title': 'Potential secrets in .env file',
                        'description': 'Verify all secrets are properly masked'
                    })

        return gaps

    def run_all_discoveries(self) -> Dict:
        """Run all gap discovery checks"""
        print("🔍 Starting comprehensive gap discovery...\n")

        all_gaps = []
        discovery_methods = [
            ('API Endpoints', self.discover_missing_endpoints),
            ('Database Setup', self.check_database_connectivity),
            ('Test Coverage', self.check_test_coverage),
            ('Docker Setup', self.check_docker_setup),
            ('Frontend Setup', self.check_frontend_setup),
            ('Critical Modules', self.check_critical_modules),
            ('Deployment Readiness', self.check_deployment_readiness),
            ('Security Configuration', self.check_security_configuration),
        ]

        for discovery_name, discovery_method in discovery_methods:
            print(f"  Checking {discovery_name}...", end=' ')
            try:
                gaps = discovery_method()
                all_gaps.extend(gaps)
                print(f"✓ ({len(gaps)} gaps)")
            except Exception as e:
                print(f"✗ (Error: {str(e)})")
                self.results['warnings'].append({
                    'discovery': discovery_name,
                    'error': str(e)
                })

        self.results['gaps'] = all_gaps

        # Generate summary statistics
        severity_counts = {}
        for gap in all_gaps:
            severity = gap.get('severity', 'UNKNOWN')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        self.results['summary'] = {
            'total_gaps': len(all_gaps),
            'by_severity': severity_counts,
            'critical_count': severity_counts.get('CRITICAL', 0),
            'high_count': severity_counts.get('HIGH', 0),
            'medium_count': severity_counts.get('MEDIUM', 0),
            'low_count': severity_counts.get('LOW', 0),
        }

        return self.results


def main():
    discovery = GapDiscovery()
    results = discovery.run_all_discoveries()

    # Print summary
    print("\n" + "="*60)
    print("GAP DISCOVERY SUMMARY")
    print("="*60)

    summary = results['summary']
    print(f"\nTotal Gaps Found: {summary['total_gaps']}")
    print(f"  CRITICAL: {summary.get('critical_count', 0)}")
    print(f"  HIGH:     {summary.get('high_count', 0)}")
    print(f"  MEDIUM:   {summary.get('medium_count', 0)}")
    print(f"  LOW:      {summary.get('low_count', 0)}")

    # Group gaps by severity
    print("\n" + "="*60)
    print("GAPS BY SEVERITY")
    print("="*60)

    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        gaps_of_severity = [g for g in results['gaps']
                            if g.get('severity') == severity]
        if gaps_of_severity:
            print(f"\n[{severity}]")
            for gap in gaps_of_severity:
                print(f"  • {gap['title']}")
                print(f"    ID: {gap.get('id', 'N/A')}")
                print(f"    Effort: {gap.get('effort', 'N/A')}")
                print(f"    Description: {gap.get('description', 'N/A')}")

    # Save detailed results
    output_file = 'gap_analysis_report.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Detailed report saved to: {output_file}")

    return results


if __name__ == '__main__':
    main()
