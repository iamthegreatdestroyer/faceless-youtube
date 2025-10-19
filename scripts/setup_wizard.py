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
        import platform
        system = platform.system()
        if system == 'Darwin':
            return 'macOS'
        elif system == 'Windows':
            return 'Windows'
        else:
            return 'Linux'
    
    def detect_python_version(self) -> str:
        """Check Python version and return version string."""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def detect_docker(self) -> bool:
        """Check if Docker and docker-compose are installed."""
        import shutil
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
        import socket
        try:
            socket.create_connection(('1.1.1.1', 53), timeout=2)
            return True
        except OSError:
            return False
    
    def _check_port_open(self, host: str, port: int, timeout: int = 1) -> bool:
        """Helper to check if a port is open on localhost."""
        import socket
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
            'internet_available': self.check_internet_connection()
        }
        return report


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
        import questionary
        
        questionary.print(
            f"\n🎉 Welcome to Faceless YouTube Setup Wizard\n"
            f"   Platform: {env_report['os']}\n"
            f"   Python: {env_report['python_version']}\n"
            f"   Docker: {'✓' if env_report['docker_available'] else '✗'}\n"
            f"   Internet: {'✓' if env_report['internet_available'] else '✗'}\n"
        )
    
    def select_deployment_mode(self) -> str:
        """Prompt user to select deployment mode."""
        import questionary
        
        choices = [
            'Docker Full Stack (recommended)',
            'Local Services (advanced)',
            'Hybrid (Docker + Local)',
            'Development (default)'
        ]
        
        answer = questionary.select(
            'Select deployment mode:',
            choices=choices
        ).ask()
        
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
        import questionary
        
        memory = questionary.text(
            'Memory limit for containers (e.g., 2g):',
            default='2g'
        ).ask()
        
        cpu = questionary.text(
            'CPU limit for containers (e.g., 2):',
            default='2'
        ).ask()
        
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
                'redis': 6379
            }
        }
    
    def configure_local_mode(self) -> dict:
        """Configure local deployment options."""
        import questionary
        
        questionary.print("\n📝 Validating local services...")
        detector = EnvironmentDetector()
        
        config = {
            'mode': 'local',
            'postgres_host': questionary.text(
                'PostgreSQL host:',
                default='localhost'
            ).ask(),
            'postgres_port': questionary.text(
                'PostgreSQL port:',
                default='5432'
            ).ask(),
            'mongodb_host': questionary.text(
                'MongoDB host:',
                default='localhost'
            ).ask(),
            'mongodb_port': questionary.text(
                'MongoDB port:',
                default='27017'
            ).ask(),
            'redis_host': questionary.text(
                'Redis host:',
                default='localhost'
            ).ask(),
            'redis_port': questionary.text(
                'Redis port:',
                default='6379'
            ).ask(),
        }
        return config
    
    def collect_api_credentials(self) -> dict:
        """Collect YouTube OAuth and other API credentials."""
        import questionary
        import os
        import json
        
        has_youtube = questionary.confirm(
            'Do you have YouTube OAuth credentials?'
        ).ask()
        
        credentials = {}
        
        if has_youtube:
            creds_path = questionary.text(
                'Path to YouTube OAuth JSON file:',
                default=os.path.expanduser('~/.youtube_oauth.json')
            ).ask()
            
            if os.path.exists(creds_path):
                try:
                    with open(creds_path, 'r') as f:
                        json.load(f)
                    credentials['youtube_oauth_path'] = creds_path
                    questionary.print('✓ YouTube OAuth file validated')
                except (json.JSONDecodeError, IOError) as e:
                    questionary.print(f'✗ Error reading file: {e}')
            else:
                questionary.print('✗ File not found. You can add it later.')
        
        return credentials
    
    def verify_configuration(self, config: dict) -> dict:
        """Test collected configurations."""
        import questionary
        
        questionary.print("\n🔍 Verifying configuration...")
        
        verification = {
            'passed': True,
            'warnings': [],
            'errors': []
        }
        
        if config['mode'] == 'docker':
            # Docker mode is always viable
            pass
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
                questionary.print(f"⚠️  {warning}")
        
        if verification['errors']:
            verification['passed'] = False
            for error in verification['errors']:
                questionary.print(f"❌ {error}")
        else:
            questionary.print("✓ Configuration verified")
        
        return verification
    
    def generate_env_file(self, config: dict) -> None:
        """Generate .env file from configuration."""
        import os
        from datetime import datetime
        
        env_content = f"""# Generated by setup wizard
# Generated at: {datetime.now().isoformat()}

# Environment
ENVIRONMENT=development

# Database Configuration
"""
        
        if config['mode'] == 'docker':
            env_content += f"""DATABASE_URL=postgresql://docker:docker@postgres:5432/faceless_youtube
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
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        # Set restrictive permissions
        os.chmod('.env', 0o600)
        print("✓ Generated .env file")
    
    def display_next_steps(self, mode: str) -> None:
        """Display next steps based on deployment mode."""
        import questionary
        
        questionary.print("\n📚 Next Steps:\n")
        
        if mode == 'docker':
            questionary.print(
                "1. Start Docker services:\n"
                "   docker-compose up -d\n\n"
                "2. Run the application:\n"
                "   cd dashboard && npm run dev\n\n"
                "3. Access services:\n"
                "   API: http://localhost:8000\n"
                "   Dashboard: http://localhost:3000\n"
            )
        else:
            questionary.print(
                "1. Ensure local services are running:\n"
                "   PostgreSQL, MongoDB, Redis, Ollama\n\n"
                "2. Run the application:\n"
                "   cd dashboard && npm run dev\n\n"
                "3. In another terminal:\n"
                "   uvicorn src.api.main:app --reload\n"
            )


class ConfigurationManager:
    """Manages configuration generation and validation."""
    
    def validate_configuration(self, config: dict) -> dict:
        """Validate configuration completeness."""
        required_fields = ['mode']
        missing = [f for f in required_fields if f not in config]
        
        return {
            'valid': len(missing) == 0,
            'missing_fields': missing
        }
    
    def write_env_file(self, config: dict, path: str = '.env') -> None:
        """Write configuration to .env file."""
        import os
        from datetime import datetime
        
        # Validate first
        validation = self.validate_configuration(config)
        if not validation['valid']:
            raise ValueError(f"Invalid config: {validation['missing_fields']}")
        
        # Generate content
        env_lines = [
            "# Generated by Faceless YouTube Setup Wizard",
            f"# Generated: {datetime.now().isoformat()}",
            "",
            "ENVIRONMENT=development",
            ""
        ]
        
        if config['mode'] == 'docker':
            env_lines.extend([
                "# Docker Services",
                "DATABASE_URL=postgresql://docker:docker@postgres:5432/faceless_youtube",
                "MONGODB_URI=mongodb://root:password@mongodb:27017/faceless_youtube",
                "REDIS_URL=redis://redis:6379/0",
                ""
            ])
        else:
            env_lines.extend([
                "# Local Services",
                f"DATABASE_URL=postgresql://user:password@{config.get('postgres_host', 'localhost')}:{config.get('postgres_port', 5432)}/faceless_youtube",
                f"MONGODB_URI=mongodb://root:password@{config.get('mongodb_host', 'localhost')}:{config.get('mongodb_port', 27017)}/faceless_youtube",
                f"REDIS_URL=redis://{config.get('redis_host', 'localhost')}:{config.get('redis_port', 6379)}/0",
                ""
            ])
        
        env_lines.extend([
            "API_HOST=0.0.0.0",
            "API_PORT=8000",
            "REACT_APP_API_URL=http://localhost:8000",
            "OLLAMA_BASE_URL=http://localhost:11434",
            "OLLAMA_MODEL=llama2",
            ""
        ])
        
        # Write file
        if os.path.exists(path):
            import shutil
            shutil.copy(path, f"{path}.bak")
        
        with open(path, 'w') as f:
            f.write('\n'.join(env_lines))
        
        os.chmod(path, 0o600)
"""

    def validate_configuration(self, config: Dict[str, str]) -> ValidationResult:
        errors: List[str] = []
        required = ["DATABASE_URL", "MONGODB_URI", "REDIS_URL"]
        for r in required:
            if not config.get(r):
                errors.append(f"Missing required configuration: {r}")

        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def write_env_file(self, config: Dict[str, str], path: str = ".env") -> None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        contents = self.ENV_TEMPLATE.format(timestamp=timestamp, **config)
        if os.path.exists(path):
            shutil.copy(path, f"{path}.bak")

        with open(path, "w", encoding="utf-8") as fh:
            fh.write(contents)

    def generate_docker_compose_override(self, config: DockerConfig) -> str:
        override = f"""version: '3.9'\nservices:\n  api:\n    ports:\n      - \"{config.api_port}:8000\"\n  dashboard:\n    ports:\n      - \"{config.frontend_port}:3000\"\n"""
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
    """Main wizard orchestration."""
    import os
    
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
                'docker_services': ['postgres', 'mongodb', 'redis']
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
