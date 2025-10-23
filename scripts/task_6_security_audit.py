#!/usr/bin/env python3
"""Task #6 Security & Performance Audit - Phase 1: Security Review."""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Configuration
SCAN_PATHS = {
    'src': 'c:\\FacelessYouTube\\src',
    'tests': 'c:\\FacelessYouTube\\tests',
}

SECURITY_PATTERNS = {
    'hardcoded_api_key': r'api[_-]?key\s*=\s*["\']([^"\']+)["\']',
    'hardcoded_password': r'(password|passwd|pwd)\s*=\s*["\']([^"\']+)["\']',
    'sql_injection_risk': r'\.format\(|f["\'].*\{',  # SQL with f-strings or .format()
    'debug_mode': r'debug\s*=\s*True',
    'print_statements': r'^\s*print\(',
    'except_bare': r'except\s*:',  # Bare except clause
    'eval_usage': r'\beval\(',
    'exec_usage': r'\bexec\(',
    'pickle_usage': r'\bpickle\.(loads|dumps)',
    'yaml_unsafe': r'yaml\.load\(',
    'insecure_random': r'random\.(random|choice|shuffle)',
}

PERFORMANCE_PATTERNS = {
    'n_plus_one': r'for\s+\w+\s+in\s+.*\.all\(\)',  # Potential N+1
    'large_query': r'\.all\(\)',  # Unfiltered .all()
    'missing_index_hint': r'\.filter\(',  # Should verify index exists
    'no_pagination': r'def.*\(.*\)\s*->.*List',  # Functions returning lists without limit
    'blocking_io': r'requests\.|urllib\.request\.|open\(',  # Potential blocking calls
}


class SecurityAuditor:
    """Comprehensive security audit for Task #6."""

    def __init__(self):
        self.findings = {
            'security': [],
            'performance': [],
            'timestamp': datetime.now().isoformat()
        }

    def scan_directory(self, path: str, patterns: Dict[str, str]) -> List[Dict]:
        """Scan directory for security/performance issues."""
        results = []
        
        try:
            for root, dirs, files in os.walk(path):
                # Skip common non-code directories
                dirs[:] = [d for d in dirs if d not in [
                    '__pycache__', '.git', 'node_modules', '.venv', 'venv'
                ]]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.ts')):
                        filepath = os.path.join(root, file)
                        results.extend(
                            self.scan_file(filepath, patterns)
                        )
        except Exception as e:
            print(f"❌ Error scanning {path}: {e}")
        
        return results

    def scan_file(self, filepath: str, patterns: Dict[str, str]) -> List[Dict]:
        """Scan individual file for patterns."""
        results = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_no, line in enumerate(lines, 1):
                for pattern_name, pattern in patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        results.append({
                            'file': filepath,
                            'line': line_no,
                            'pattern': pattern_name,
                            'content': line.strip()[:80]
                        })
        except Exception as e:
            print(f"❌ Error scanning file {filepath}: {e}")
        
        return results

    def audit_authentication(self) -> Dict:
        """Audit authentication implementation."""
        findings = {
            'name': 'Authentication & Authorization',
            'checks': []
        }
        
        try:
            # Check for JWT implementation
            jwt_files = []
            for root, dirs, files in os.walk(SCAN_PATHS['src']):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        with open(filepath, 'r') as f:
                            content = f.read()
                            if 'jwt' in content.lower() or 'token' in content.lower():
                                jwt_files.append(filepath)
            
            findings['checks'].append({
                'name': 'JWT Implementation',
                'status': '✓ Found' if jwt_files else '✗ Not found',
                'details': f'{len(jwt_files)} files with JWT/token logic'
            })
            
            # Check for password hashing
            for root, dirs, files in os.walk(SCAN_PATHS['src']):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        with open(filepath, 'r') as f:
                            content = f.read()
                            if 'bcrypt' in content or 'argon2' in content:
                                findings['checks'].append({
                                    'name': 'Password Hashing',
                                    'status': '✓ Secure hashing',
                                    'details': 'Using strong hash algorithm'
                                })
                                break
        
        except Exception as e:
            print(f"❌ Error in auth audit: {e}")
        
        return findings

    def audit_input_validation(self) -> Dict:
        """Audit input validation."""
        findings = {
            'name': 'Input Validation & Sanitization',
            'checks': []
        }
        
        try:
            # Check for pydantic models
            pydantic_found = False
            for root, dirs, files in os.walk(SCAN_PATHS['src']):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        with open(filepath, 'r') as f:
                            if 'pydantic' in f.read() or 'BaseModel' in f.read():
                                pydantic_found = True
                                break
            
            findings['checks'].append({
                'name': 'Schema Validation',
                'status': '✓ Pydantic used' if pydantic_found else '⚠ Consider Pydantic',
                'details': 'Request validation via schema'
            })
            
            # Check for SQL parameterization
            sql_issues = 0
            sql_files = 0
            for root, dirs, files in os.walk(SCAN_PATHS['src']):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        with open(filepath, 'r') as f:
                            content = f.read()
                            if 'sql' in content.lower() or 'query' in content.lower():
                                sql_files += 1
                                if '.format(' in content or 'f"' in content:
                                    sql_issues += 1
            
            findings['checks'].append({
                'name': 'SQL Injection Prevention',
                'status': '✓ Parameterized' if sql_issues == 0 else f'⚠ {sql_issues} potential issues',
                'details': f'Reviewed {sql_files} SQL files'
            })
        
        except Exception as e:
            print(f"❌ Error in input validation audit: {e}")
        
        return findings

    def audit_data_protection(self) -> Dict:
        """Audit data protection measures."""
        findings = {
            'name': 'Data Protection',
            'checks': []
        }
        
        try:
            # Check for secrets in environment
            env_files = []
            for fname in ['requirements.txt', '.env', '.env.example']:
                fpath = os.path.join('c:\\FacelessYouTube', fname)
                if os.path.exists(fpath):
                    env_files.append(fname)
            
            findings['checks'].append({
                'name': 'Environment Configuration',
                'status': '✓ Environment-based' if env_files else '⚠ Check config',
                'details': f'{len(env_files)} config files found'
            })
            
            # Check for encryption
            encryption_found = False
            for root, dirs, files in os.walk(SCAN_PATHS['src']):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        with open(filepath, 'r') as f:
                            content = f.read()
                            if 'cryptography' in content or 'encrypt' in content.lower():
                                encryption_found = True
                                break
            
            findings['checks'].append({
                'name': 'Data Encryption',
                'status': '✓ Encryption available' if encryption_found else '📋 Consider encryption',
                'details': 'For sensitive data at rest'
            })
        
        except Exception as e:
            print(f"❌ Error in data protection audit: {e}")
        
        return findings

    def audit_error_handling(self) -> Dict:
        """Audit error handling and logging."""
        findings = {
            'name': 'Error Handling & Logging',
            'checks': []
        }
        
        try:
            # Check for proper exception handling
            bare_excepts = self.scan_directory(
                SCAN_PATHS['src'],
                {'bare_except': r'except\s*:'}
            )
            
            findings['checks'].append({
                'name': 'Exception Handling',
                'status': '✓ Good' if len(bare_excepts) == 0 else f'⚠ {len(bare_excepts)} bare excepts',
                'details': 'Specific exception types recommended'
            })
            
            # Check for debug mode
            debug_issues = self.scan_directory(
                SCAN_PATHS['src'],
                {'debug_mode': r'debug\s*=\s*True'}
            )
            
            findings['checks'].append({
                'name': 'Debug Mode',
                'status': '✓ Disabled' if len(debug_issues) == 0 else f'⚠ {len(debug_issues)} debug=True',
                'details': 'Should be False in production'
            })
            
            # Check for logging
            logging_found = False
            for root, dirs, files in os.walk(SCAN_PATHS['src']):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        with open(filepath, 'r') as f:
                            if 'logging' in f.read() or 'logger' in f.read():
                                logging_found = True
                                break
            
            findings['checks'].append({
                'name': 'Logging Implementation',
                'status': '✓ Logging configured' if logging_found else '⚠ Add logging',
                'details': 'For debugging and monitoring'
            })
        
        except Exception as e:
            print(f"❌ Error in error handling audit: {e}")
        
        return findings

    def run_audit(self) -> Dict:
        """Run complete security audit."""
        print('\n' + '=' * 60)
        print('TASK #6: SECURITY AUDIT - PHASE 1')
        print('=' * 60 + '\n')
        
        audit_results = []
        
        # Run security scans
        print('🔍 Authentication & Authorization...')
        audit_results.append(self.audit_authentication())
        
        print('🔍 Input Validation & Sanitization...')
        audit_results.append(self.audit_input_validation())
        
        print('🔍 Data Protection...')
        audit_results.append(self.audit_data_protection())
        
        print('🔍 Error Handling & Logging...')
        audit_results.append(self.audit_error_handling())
        
        # Scan for patterns
        print('\n📊 Security Pattern Scan...')
        security_patterns = self.scan_directory(SCAN_PATHS['src'], SECURITY_PATTERNS)
        
        print('📊 Performance Pattern Scan...')
        perf_patterns = self.scan_directory(SCAN_PATHS['src'], PERFORMANCE_PATTERNS)
        
        # Summary
        print('\n' + '=' * 60)
        print('AUDIT RESULTS SUMMARY')
        print('=' * 60 + '\n')
        
        for result in audit_results:
            print(f"\n{result['name']}:")
            for check in result['checks']:
                print(f"  {check['status']}")
                print(f"    → {check['details']}")
        
        print(f'\n📊 Security issues found: {len(security_patterns)}')
        print(f'📊 Performance issues found: {len(perf_patterns)}')
        
        # Save results
        audit_output = {
            'timestamp': datetime.now().isoformat(),
            'security_audit': audit_results,
            'security_patterns': len(security_patterns),
            'performance_patterns': len(perf_patterns),
            'details': {
                'security': security_patterns[:10],  # First 10
                'performance': perf_patterns[:10]
            }
        }
        
        with open('TASK_6_SECURITY_AUDIT_RESULTS.json', 'w') as f:
            json.dump(audit_output, f, indent=2)
        
        print('\n✓ Results saved to TASK_6_SECURITY_AUDIT_RESULTS.json')
        
        return audit_output


if __name__ == '__main__':
    auditor = SecurityAuditor()
    results = auditor.run_audit()
