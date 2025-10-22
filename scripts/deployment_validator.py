#!/usr/bin/env python3
"""
Comprehensive System Deployment Validation
Validates all components of Faceless YouTube system are production-ready
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict


class DeploymentValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'validations': {},
            'blockers': [],
            'warnings': [],
            'ready_for_production': False
        }

    def check_python_version(self) -> Dict:
        """Verify Python 3.13 is available"""
        version = sys.version_info
        is_valid = version.major == 3 and version.minor >= 13

        return {
            'name': 'Python Version',
            'status': 'PASS' if is_valid else 'FAIL',
            'details': (f'Python {version.major}.{version.minor}.'
                        f'{version.micro}'),
            'required': '>= 3.13',
            'severity': 'CRITICAL' if not is_valid else 'INFO'
        }

    def check_dependencies(self) -> Dict:
        """Verify critical dependencies are installed"""
        required = {
            'fastapi': 'API Framework',
            'uvicorn': 'ASGI Server',
            'sqlalchemy': 'ORM',
            'pydantic': 'Data Validation',
            'psycopg2': 'PostgreSQL',
            'pymongo': 'MongoDB',
            'redis': 'Cache',
            'anthropic': 'Claude API',
        }

        missing = []
        for module, description in required.items():
            try:
                __import__(module)
            except ImportError:
                missing.append(module)

        status = 'PASS' if len(missing) == 0 else 'FAIL'
        details = f'{len(required) - len(missing)}/{len(required)} available'

        if missing:
            details += f' (missing: {", ".join(missing)})'

        return {
            'name': 'Dependencies',
            'status': status,
            'details': details,
            'severity': 'CRITICAL' if missing else 'INFO'
        }

    def check_database_files(self) -> Dict:
        """Verify database migration and model files exist"""
        required_files = {
            'alembic.ini': 'Database migrations config',
            'src/database/postgres.py': 'PostgreSQL integration',
            'src/core/models.py': 'Data models',
            'src/core/__init__.py': 'Core package',
        }

        missing = []
        for filepath, description in required_files.items():
            full_path = self.project_root / filepath
            if not full_path.exists():
                missing.append((filepath, description))

        status = 'PASS' if len(missing) == 0 else 'FAIL'
        details = (f'{len(required_files) - len(missing)}/'
                   f'{len(required_files)} present')

        if missing:
            details += f' (missing: {", ".join([f[0] for f in missing])})'

        return {
            'name': 'Database Configuration',
            'status': status,
            'details': details,
            'severity': 'CRITICAL' if missing else 'INFO'
        }

    def check_api_structure(self) -> Dict:
        """Verify API is properly structured"""
        required_endpoints = {
            '/health': 'Health check',
            '/api/health': 'API health',
            '/api/jobs': 'Job management',
            '/api/videos': 'Video management',
            '/api/auth': 'Authentication',
        }

        main_py = self.project_root / 'src' / 'api' / 'main.py'
        if not main_py.exists():
            return {
                'name': 'API Structure',
                'status': 'FAIL',
                'details': 'src/api/main.py not found',
                'severity': 'CRITICAL'
            }

        with open(main_py, 'r') as f:
            content = f.read()

        found = sum(1 for endpoint in required_endpoints.keys()
                    if endpoint in content)
        total = len(required_endpoints)

        status = 'PASS' if found == total else 'WARN'

        return {
            'name': 'API Structure',
            'status': status,
            'details': f'{found}/{total} required endpoints defined',
            'severity': 'HIGH' if found < 3 else 'INFO'
        }

    def check_environment_config(self) -> Dict:
        """Verify environment configuration"""
        env_file = self.project_root / '.env'

        if not env_file.exists():
            return {
                'name': 'Environment Config',
                'status': 'WARN',
                'details': '.env file not found (use setup wizard to create)',
                'severity': 'MEDIUM'
            }

        required_vars = [
            'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER',
            'API_PORT', 'ANTHROPIC_API_KEY',
            'MONGODB_URL'
        ]

        with open(env_file, 'r') as f:
            env_content = f.read()

        missing = [var for var in required_vars if var not in env_content]

        status = 'PASS' if len(missing) == 0 else 'FAIL'
        details = f'{len(required_vars) - len(missing)}/{len(required_vars)}'

        if missing:
            details += f' (missing: {", ".join(missing)})'

        return {
            'name': 'Environment Config',
            'status': status,
            'details': details,
            'severity': 'CRITICAL' if missing else 'INFO'
        }

    def check_frontend_setup(self) -> Dict:
        """Verify frontend is configured"""
        dashboard_dir = self.project_root / 'dashboard'
        package_json = dashboard_dir / 'package.json'

        if not dashboard_dir.exists():
            return {
                'name': 'Frontend Setup',
                'status': 'FAIL',
                'details': 'dashboard/ directory not found',
                'severity': 'HIGH'
            }

        if not package_json.exists():
            return {
                'name': 'Frontend Setup',
                'status': 'FAIL',
                'details': 'package.json not found',
                'severity': 'HIGH'
            }

        return {
            'name': 'Frontend Setup',
            'status': 'PASS',
            'details': 'React/Next.js project configured',
            'severity': 'INFO'
        }

    def check_docker_setup(self) -> Dict:
        """Verify Docker configuration for deployment"""
        required_files = {
            'docker-compose.yml': 'Development stack',
            'docker-compose.staging.yml': 'Staging stack',
            'Dockerfile.prod': 'Production build',
        }

        missing = []
        for filename, description in required_files.items():
            if not (self.project_root / filename).exists():
                missing.append(filename)

        status = 'PASS' if len(missing) == 0 else 'WARN'
        details = f'{len(required_files) - len(missing)}/{len(required_files)}'

        if missing:
            details += f' (missing: {", ".join(missing)})'

        return {
            'name': 'Docker Configuration',
            'status': status,
            'details': details,
            'severity': 'MEDIUM' if missing else 'INFO'
        }

    def check_test_suite(self) -> Dict:
        """Verify testing infrastructure"""
        tests_dir = self.project_root / 'tests'

        if not tests_dir.exists():
            return {
                'name': 'Test Suite',
                'status': 'FAIL',
                'details': 'tests/ directory not found',
                'severity': 'MEDIUM'
            }

        test_files = list(tests_dir.rglob('test_*.py'))
        status = 'PASS' if len(test_files) > 0 else 'WARN'

        return {
            'name': 'Test Suite',
            'status': status,
            'details': f'{len(test_files)} test files found',
            'severity': 'HIGH' if len(test_files) < 3 else 'INFO'
        }

    def check_documentation(self) -> Dict:
        """Verify deployment documentation"""
        required_docs = {
            'README.md': 'Project README',
            'CONTRIBUTING.md': 'Contribution guidelines',
            'DEPLOYMENT_GUIDE.md': 'Deployment instructions',
        }

        found = 0
        for filename, description in required_docs.items():
            if (self.project_root / filename).exists():
                found += 1

        status = 'PASS' if found >= 2 else 'WARN'
        details = f'{found}/{len(required_docs)} documentation files'

        return {
            'name': 'Documentation',
            'status': status,
            'details': details,
            'severity': 'LOW'
        }

    def check_git_status(self) -> Dict:
        """Verify git repository is clean"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return {
                    'name': 'Git Status',
                    'status': 'WARN',
                    'details': 'Not a git repository',
                    'severity': 'LOW'
                }

            uncommitted = len(result.stdout.strip().split('\n'))
            status = 'WARN' if uncommitted > 0 else 'PASS'

            return {
                'name': 'Git Status',
                'status': status,
                'details': (f'{uncommitted} uncommitted changes'
                            if uncommitted > 0 else 'Clean'),
                'severity': 'LOW'
            }

        except Exception as e:
            return {
                'name': 'Git Status',
                'status': 'WARN',
                'details': f'Could not check: {str(e)}',
                'severity': 'LOW'
            }

    def run_all_validations(self) -> Dict:
        """Run all deployment validations"""
        print("🔍 Running deployment validation checks...\n")

        validators = [
            ('Python Version', self.check_python_version),
            ('Dependencies', self.check_dependencies),
            ('Database', self.check_database_files),
            ('API', self.check_api_structure),
            ('Environment', self.check_environment_config),
            ('Frontend', self.check_frontend_setup),
            ('Docker', self.check_docker_setup),
            ('Tests', self.check_test_suite),
            ('Documentation', self.check_documentation),
            ('Git', self.check_git_status),
        ]

        passed = 0
        failed = 0
        warnings = 0

        for check_name, check_func in validators:
            print(f"  Checking {check_name}...", end=' ')
            try:
                result = check_func()
                self.results['validations'][check_name] = result

                if result['status'] == 'PASS':
                    print("✓ PASS")
                    passed += 1
                elif result['status'] == 'FAIL':
                    print("✗ FAIL")
                    failed += 1
                    if result.get('severity') == 'CRITICAL':
                        self.results['blockers'].append(check_name)
                else:  # WARN
                    print("⚠ WARN")
                    warnings += 1
                    self.results['warnings'].append(check_name)

            except Exception as e:
                print(f"✗ ERROR: {str(e)}")
                failed += 1

        # Determine production readiness
        self.results['ready_for_production'] = (
            failed == 0 and len(self.results['blockers']) == 0
        )

        self.results['summary'] = {
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'total': len(validators),
            'blockers': len(self.results['blockers']),
            'production_ready': self.results['ready_for_production']
        }

        return self.results


def main():
    validator = DeploymentValidator()
    results = validator.run_all_validations()

    print("\n" + "="*60)
    print("DEPLOYMENT VALIDATION SUMMARY")
    print("="*60)

    summary = results['summary']
    print(f"\nValidations: {summary['passed']} passed, "
          f"{summary['failed']} failed, "
          f"{summary['warnings']} warnings")

    if results['blockers']:
        print(f"\n🚨 BLOCKERS ({len(results['blockers'])}):")
        for blocker in results['blockers']:
            validation = results['validations'].get(blocker, {})
            print(f"  ✗ {blocker}: {validation.get('details', 'Unknown')}")

    if results['warnings']:
        print(f"\n⚠️  WARNINGS ({len(results['warnings'])}):")
        for warning in results['warnings']:
            validation = results['validations'].get(warning, {})
            print(f"  • {warning}: {validation.get('details', 'Unknown')}")

    print("\n" + "="*60)
    if results['ready_for_production']:
        print("✅ PRODUCTION READY")
    else:
        print("❌ NOT PRODUCTION READY")
        print(f"Fix {summary['blockers']} blocker(s) before deployment")
    print("="*60)

    # Save detailed results
    output_file = 'deployment_validation_report.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Detailed report saved to: {output_file}\n")

    return results


if __name__ == '__main__':
    main()
