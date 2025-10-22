#!/usr/bin/env python3
"""Interactive setup wizard for Faceless YouTube project.

Features:
- Environment detection (OS, Python, Docker, common services)
- Interactive deployment mode selection (Docker/Local/Hybrid)
- Service configuration prompts
- API credentials collection and validation (YouTube OAuth)
- Verification and .env file generation

This wizard is intentionally conservative and provides fallbacks where
automated verification is not possible.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    import questionary
except Exception:  # pragma: no cover - interactive dependency
    questionary = None


def _q_print(message: str) -> None:
    """Print using questionary when available, otherwise fallback.

    This keeps calling sites simple and avoids repeating checks.
    """
    if questionary:
        try:
            questionary.print(message)
            return
        except Exception:
            pass
    print(message)


def _q_text(prompt: str, default: Optional[str] = None) -> str:
    """Ask for free-text input using questionary or input()."""
    if questionary:
        try:
            return questionary.text(prompt, default=default).ask() or (default or '')
        except Exception:
            pass

    default_display = f" [{default}]" if default else ''
    return input(f"{prompt}{default_display}: ").strip() or (default or '')


def _q_select(prompt: str, choices: List[str], default: Optional[str] = None) -> str:
    """Prompt the user to select an option from a list.

    Falls back to a numbered prompt when questionary is unavailable.
    """
    if questionary:
        try:
            return questionary.select(prompt, choices=choices).ask() or (default or choices[-1])
        except Exception:
            pass

    print(prompt)
    for i, c in enumerate(choices, start=1):
        print(f"  {i}. {c}")
    sel = input(f"Enter number (default {default or len(choices)}): ").strip() or ''
    try:
        idx = int(sel) - 1
        return choices[idx]
    except Exception:
        return default or choices[-1]


def _q_confirm(prompt: str, default: bool = False) -> bool:
    """Ask a yes/no question, returning True/False."""
    if questionary:
        try:
            return questionary.confirm(prompt, default=default).ask()
        except Exception:
            pass

    default_str = 'Y/n' if default else 'y/N'
    resp = input(f"{prompt} [{default_str}]: ").strip().lower()
    if resp == '':
        return default
    return resp in ('y', 'yes')


@dataclass
class EnvironmentReport:
    os: str
    python_version: str
    docker_installed: bool
    docker_compose_installed: bool
    postgres_running: bool
    mongodb_running: bool
    redis_running: bool
    ollama_running: bool
    internet: bool
    details: Dict[str, str] = field(default_factory=dict)


class EnvironmentDetector:
    """Detects system capabilities and existing services."""
    
    def detect_os(self) -> str:
        """Detect operating system: Windows, macOS, or Linux."""
        system = platform.system()
        if system == 'Darwin':
            return 'macOS'
        elif system == 'Windows':
            return 'Windows'
        else:
            return 'Linux'
    
    def detect_python_version(self) -> str:
        """Check Python version and return version string."""
        v = sys.version_info
        return f"{v.major}.{v.minor}.{v.micro}"
    
    def detect_docker(self) -> bool:
        """Check if Docker and docker-compose are installed."""
        docker_exists = shutil.which('docker') is not None
        compose_exists = (
            shutil.which('docker-compose') is not None or
            shutil.which('docker') is not None  # docker compose (v2)
        )
        return docker_exists and compose_exists
    
    def detect_postgresql(self) -> bool:
        """Check if PostgreSQL is running locally on port 5432."""
        return self._check_port_open('localhost', 5432)
    
    def detect_mongodb(self) -> bool:
        """Check if MongoDB is running locally on port 27017."""
        return self._check_port_open('localhost', 27017)
    
    def detect_redis(self) -> bool:
        """Check if Redis is running locally on port 6379."""
        return self._check_port_open('localhost', 6379)
    
    def detect_ollama(self) -> bool:
        """Check if Ollama is running locally on port 11434."""
        return self._check_port_open('localhost', 11434)
    
    def check_internet_connection(self) -> bool:
        """Verify internet connectivity for GitHub/Docker Hub access."""
        try:
            socket.create_connection(('1.1.1.1', 53), timeout=2)
            return True
        except OSError:
            return False
    
    def _check_port_open(self, host: str, port: int, timeout: int = 1) -> bool:
        """Helper to check if a port is open on localhost."""
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.close()
            return True
        except (socket.timeout, OSError):
            return False
    
    def generate_report(self) -> dict:
        """Generate comprehensive environment snapshot."""
        return {
            'os': self.detect_os(),
            'python_version': self.detect_python_version(),
            'docker_available': self.detect_docker(),
            'postgresql_running': self.detect_postgresql(),
            'mongodb_running': self.detect_mongodb(),
            'redis_running': self.detect_redis(),
            'ollama_running': self.detect_ollama(),
            'internet_available': self.check_internet_connection(),
        }


@dataclass
class DockerConfig:
    memory_mb: int = 4096
    cpu_shares: int = 2
    api_port: int = 8000
    frontend_port: int = 3000


@dataclass
class LocalConfig:
    postgres_url: Optional[str] = None
    mongodb_uri: Optional[str] = None
    redis_url: Optional[str] = None


@dataclass
class ValidationResult:
    passed: bool
    errors: List[str] = field(default_factory=list)


class InteractiveWizard:
    """Guides user through interactive setup process."""
    
    def welcome_screen(self, env_report: dict) -> None:
        """Display welcome and environment summary."""
        msg = (
            f"\n🎉 Welcome to Faceless YouTube Setup Wizard\n"
            f"   Platform: {env_report['os']}\n"
            f"   Python: {env_report['python_version']}\n"
            f"   Docker: {'✓' if env_report['docker_available'] else '✗'}\n"
            f"   Internet: {'✓' if env_report['internet_available'] else '✗'}\n"
        )

        _q_print(msg)
    
    def select_deployment_mode(self) -> str:
        """Prompt user to select deployment mode."""
        choices = [
            'Docker Full Stack (recommended)',
            'Local Services (advanced)',
            'Hybrid (Docker + Local)',
            'Development (default)'
        ]
        answer = _q_select('Select deployment mode:', choices, default='Development (default)')

        # Map display names to enum values
        mode_map = {
            'Docker Full Stack (recommended)': 'docker',
            'Local Services (advanced)': 'local',
            'Hybrid (Docker + Local)': 'hybrid',
            'Development (default)': 'development'
        }
        return mode_map.get(answer, 'development')
    
    def configure_docker_mode(self) -> dict:
        """Configure Docker deployment options."""
        # Use questionary if available, otherwise fallback to input()
        memory = _q_text('Memory limit for containers (e.g., 2g):', default='2g')
        cpu = _q_text('CPU limit for containers (e.g., 2):', default='2')

        return {
            'mode': 'docker',
            'memory': memory,
            'cpu': cpu,
            'volumes': True,
            'ports': {
                'api': 8000,
                'frontend': 3000,
                'postgres': 5432,
                'mongodb': 27017,
                'redis': 6379,
            },
        }
    
    def configure_local_mode(self) -> dict:
        """Configure local deployment options."""
        _q_print("\n📝 Validating local services...")
        detector = EnvironmentDetector()

        # Prompt for local connection settings using the helper wrapper
        config = {
            'mode': 'local',
            'postgres_host': _q_text('PostgreSQL host:', default='localhost'),
            'postgres_port': _q_text('PostgreSQL port:', default='5432'),
            'mongodb_host': _q_text('MongoDB host:', default='localhost'),
            'mongodb_port': _q_text('MongoDB port:', default='27017'),
            'redis_host': _q_text('Redis host:', default='localhost'),
            'redis_port': _q_text('Redis port:', default='6379'),
        }

        # Quick detection summary
        try:
            pg_ok = detector.detect_postgresql()
            mongo_ok = detector.detect_mongodb()
            redis_ok = detector.detect_redis()
        except Exception:
            pg_ok = mongo_ok = redis_ok = False

        summary = (
            f"Detected services -> Postgres: {'yes' if pg_ok else 'no'}, "
            f"MongoDB: {'yes' if mongo_ok else 'no'}, Redis: {'yes' if redis_ok else 'no'}"
        )
        _q_print(summary)

        return config
    
    def collect_api_credentials(self) -> dict:
        """Collect YouTube OAuth and other API credentials."""
        # Use questionary where available, otherwise fallback to input()
        has_youtube = _q_confirm('Do you have YouTube OAuth credentials?', default=False)
        
        credentials = {}
        
        if has_youtube:
            creds_path = _q_text('Path to YouTube OAuth JSON file:', default=os.path.expanduser('~/.youtube_oauth.json'))
            
            if os.path.exists(creds_path):
                try:
                    with open(creds_path, 'r') as f:
                        json.load(f)
                    credentials['youtube_oauth_path'] = creds_path
                    _q_print('✓ YouTube OAuth file validated')
                except (json.JSONDecodeError, IOError) as e:
                    _q_print(f'✗ Error reading file: {e}')
            else:
                _q_print('✗ File not found. You can add it later.')
        
        return credentials
    
    def verify_configuration(self, config: dict) -> dict:
        """Test collected configurations."""
        # Use questionary for pretty output when available
        _q_print("\n🔍 Verifying configuration...")
        
        verification = {
            'passed': True,
            'warnings': [],
            'errors': []
        }
        
        if config['mode'] == 'docker':
            # Sanity-check docker availability when the user chooses Docker mode
            detector = EnvironmentDetector()
            if not detector.detect_docker():
                verification['errors'].append(
                    'Docker not detected on this system. Please install Docker and docker-compose.'
                )
                verification['passed'] = False
        elif config['mode'] == 'local':
            # Verify local services
            detector = EnvironmentDetector()
            
            if not detector.detect_postgresql():
                verification['warnings'].append(
                    'PostgreSQL not detected on localhost:5432'
                )
            if not detector.detect_mongodb():
                verification['warnings'].append(
                    'MongoDB not detected on localhost:27017'
                )
            if not detector.detect_redis():
                verification['warnings'].append(
                    'Redis not detected on localhost:6379'
                )
        
        if verification['warnings']:
            for warning in verification['warnings']:
                _q_print(f"⚠️  {warning}")
        
        if verification['errors']:
            verification['passed'] = False
            for error in verification['errors']:
                _q_print(f"❌ {error}")
        else:
            _q_print("✓ Configuration verified")
        
        return verification
    
    def generate_env_file(self, config: dict) -> None:
        """Generate .env file from configuration."""
        from datetime import datetime
        
        env_content = f"""# Generated by setup wizard
# Generated at: {datetime.now().isoformat()}

# Environment
ENVIRONMENT=development

# Database Configuration
"""
        
        if config['mode'] == 'docker':
            env_content += """DATABASE_URL=postgresql://docker:docker@postgres:5432/faceless_youtube
MONGODB_URI=mongodb://root:password@mongodb:27017/faceless_youtube
REDIS_URL=redis://redis:6379/0
"""
        else:
            env_content += f"""DATABASE_URL=postgresql://user:password@{config.get('postgres_host', 'localhost')}:{config.get('postgres_port', 5432)}/faceless_youtube
MONGODB_URI=mongodb://root:password@{config.get('mongodb_host', 'localhost')}:{config.get('mongodb_port', 27017)}/faceless_youtube
REDIS_URL=redis://{config.get('redis_host', 'localhost')}:{config.get('redis_port', 6379)}/0
"""
        
        env_content += """
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000

# AI Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Logging
LOG_LEVEL=INFO

# Debug
DEBUG=False
"""
        
        # Backup existing .env if present
        if os.path.exists('.env'):
            import shutil
            shutil.copy('.env', '.env.bak')
            print("✓ Backed up existing .env to .env.bak")

        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)

        # Set restrictive permissions where possible
        try:
            os.chmod('.env', 0o600)
        except OSError:
            print('⚠️ Could not set POSIX permissions on .env; continuing')
        print("✓ Generated .env file")
    
    def display_next_steps(self, mode: str) -> None:
        """Display next steps based on deployment mode."""
        header = "\n📚 Next Steps:\n"

        _q_print(header)

        if mode == 'docker':
            msg = (
                "1. Start Docker services:\n"
                "   docker-compose up -d\n\n"
                "2. Run the application:\n"
                "   cd dashboard && npm run dev\n\n"
                "3. Access services:\n"
                "   API: http://localhost:8000\n"
                "   Dashboard: http://localhost:3000\n"
            )
        else:
            msg = (
                "1. Ensure local services are running:\n"
                "   PostgreSQL, MongoDB, Redis, Ollama\n\n"
                "2. Run the application:\n"
                "   cd dashboard && npm run dev\n\n"
                "3. In another terminal:\n"
                "   uvicorn src.api.main:app --reload\n"
            )

        _q_print(msg)


class ConfigurationManager:
    """Manages configuration generation and validation.

    Uses ValidationResult for validation reporting and provides
    helpers to write a `.env` file and create a minimal
    docker-compose override for local port mappings.
    """

    def validate_configuration(self, config: Dict[str, str]) -> ValidationResult:
        """Validate that required configuration keys are present.

        For `local` mode the host/port pairs for PostgreSQL,
        MongoDB, and Redis are required. For other modes a
        DATABASE_URL, MONGODB_URI or REDIS_URL may be present
        and will be validated if provided.
        """
        errors: List[str] = []
        mode = config.get('mode', 'development')

        if mode == 'local':
            required = [
                'postgres_host', 'postgres_port',
                'mongodb_host', 'mongodb_port',
                'redis_host', 'redis_port'
            ]
            for key in required:
                if not config.get(key):
                    errors.append(f"Missing required field: {key}")
        else:
            # If explicit connection strings are expected, ensure they exist
            for key in ('DATABASE_URL', 'MONGODB_URI', 'REDIS_URL'):
                if key in config and not config.get(key):
                    errors.append(f"Missing required configuration: {key}")

        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def write_env_file(self, config: Dict[str, str], path: str = '.env') -> None:
        """Write a `.env` file to disk, backing up any existing file.

        The function is tolerant of platforms without POSIX permissions.
        """
        lines: List[str] = [
            '# Generated by Faceless YouTube Setup Wizard',
            f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            '',
        ]

        # Basic environment
        lines.append(f"ENVIRONMENT={config.get('mode', 'development')}")

        # Connection strings
        if config.get('mode') in ('docker', 'hybrid'):
            lines.extend([
                'DATABASE_URL=postgresql://docker:docker@postgres:5432/faceless_youtube',
                'MONGODB_URI=mongodb://root:password@mongodb:27017/faceless_youtube',
                'REDIS_URL=redis://redis:6379/0',
            ])
        else:
            lines.extend([
                f"DATABASE_URL={config.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/faceless_youtube')}",
                f"MONGODB_URI={config.get('MONGODB_URI', 'mongodb://root:password@localhost:27017/faceless_youtube')}",
                f"REDIS_URL={config.get('REDIS_URL', 'redis://localhost:6379/0')}",
            ])

        # Common settings
        lines.extend([
            '',
            'API_HOST=0.0.0.0',
            'API_PORT=8000',
            'REACT_APP_API_URL=http://localhost:8000',
            'OLLAMA_BASE_URL=http://localhost:11434',
            'OLLAMA_MODEL=llama2',
            '',
            'LOG_LEVEL=INFO',
            'DEBUG=False',
        ])

        # Backup existing file
        if os.path.exists(path):
            bak = f"{path}.bak"
            shutil.copy(path, bak)
            print(f"✓ Backed up existing {path} to {bak}")

        with open(path, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')

        try:
            os.chmod(path, 0o600)
        except OSError:
            # Ignore on platforms that do not support chmod
            print(f"⚠️ Could not set POSIX permissions on {path}; continuing")

        print(f"✓ Wrote configuration to {path}")

    def generate_docker_compose_override(self, config: DockerConfig) -> str:
        """Generate a minimal docker-compose override YAML snippet
        that maps API and dashboard ports to host ports.
        """
        override = (
            "version: '3.9'\n"
            "services:\n"
            f"  api:\n    ports:\n      - \"{config.api_port}:8000\"\n"
            f"  dashboard:\n    ports:\n      - \"{config.frontend_port}:3000\"\n"
        )
        return override


class DockerSetupHelper:
    def check_docker_installation(self) -> bool:
        return shutil.which("docker") is not None

    def pull_required_images(self) -> None:
        images = [
            "postgres:15-alpine",
            "mongo:6.0",
            "redis:7-alpine",
            "node:18-alpine",
        ]
        for img in images:
            subprocess.run(["docker", "pull", img], check=False)

    def validate_docker_resources(self) -> Dict[str, str]:
        # Minimal heuristics for demo purposes
        return {
            "disk_space": "unknown",
            "memory": "unknown",
            "cpu": "unknown",
        }

    def generate_docker_compose_override(self, config: DockerConfig) -> str:
        return ConfigurationManager().generate_docker_compose_override(config)

    def startup_docker_stack(self, config: DockerConfig) -> Dict[str, str]:
        # Minimal orchestrator — just call docker-compose with default files
        try:
            subprocess.run(["docker-compose", "up", "-d"], check=True)
            return {"status": "started"}
        except Exception as exc:
            return {"status": "failed", "error": str(exc)}


def main() -> int:
    """Main wizard orchestration.

    Orchestrates environment detection, interactive prompts,
    verification and file generation. Returns 0 on success and
    non-zero on failure.
    """
    try:
        # Phase 1: Environment detection
        detector = EnvironmentDetector()
        env_report = detector.generate_report()

        # Phase 2: Welcome screen
        wizard = InteractiveWizard()
        wizard.welcome_screen(env_report)

        # Phase 3: Deployment mode selection
        mode = wizard.select_deployment_mode()

        # Phase 4: Configuration based on mode
        if mode == 'docker':
            config = wizard.configure_docker_mode()
        elif mode == 'local':
            config = wizard.configure_local_mode()
        else:  # hybrid or development
            config = {
                'mode': mode,
                'use_docker': True,
                'docker_services': ['postgres', 'mongodb', 'redis'],
            }

        # Phase 5: API credentials
        api_creds = wizard.collect_api_credentials()
        config.update(api_creds)

        # Phase 6: Verification
        verification = wizard.verify_configuration(config)
        if not verification['passed']:
            return 1

        # Phase 7: Generate files
        cfg_mgr = ConfigurationManager()
        cfg_mgr.write_env_file(config)

        # Phase 7b: Generate docker-compose.override.yml for Docker mode
        if mode == 'docker':
            docker_config = DockerConfig(
                memory_mb=int(config.get('memory', '2g').rstrip('g')) * 1024 if 'g' in config.get('memory', '2g') else 4096,
                cpu_shares=int(config.get('cpu', 2)),
                api_port=config.get('api_port', 8000),
                frontend_port=config.get('frontend_port', 3000),
            )
            override_content = cfg_mgr.generate_docker_compose_override(docker_config)
            override_path = 'docker-compose.override.yml'

            if os.path.exists(override_path):
                shutil.copy(override_path, f"{override_path}.bak")
                print(f"✓ Backed up existing {override_path} to {override_path}.bak")

            with open(override_path, 'w', encoding='utf-8') as f:
                f.write(override_content)
            print(f"✓ Wrote Docker Compose override to {override_path}")

        # Phase 8: Display next steps
        wizard.display_next_steps(mode)

        print("✅ Setup wizard completed successfully!")
        return 0

    except KeyboardInterrupt:
        print("\n⚠️ Setup wizard interrupted by user.")
        return 130
    except Exception as e:
        print(f"❌ Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
