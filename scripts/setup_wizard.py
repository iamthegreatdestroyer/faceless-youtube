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
    """Detects system capabilities and existing services.

    Methods return minimal, serializable values so the interactive UI can
    present them concisely.
    """

    def detect_os(self) -> str:
        return platform.system()

    def detect_python_version(self) -> str:
        return platform.python_version()

    def detect_docker(self) -> bool:
        return shutil.which("docker") is not None

    def detect_docker_compose(self) -> bool:
        # docker-compose could be the standalone binary or 'docker compose'
        return shutil.which("docker-compose") is not None or shutil.which("docker") is not None

    def _check_port(self, host: str, port: int, timeout: float = 0.5) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    def detect_postgresql(self) -> bool:
        return self._check_port("localhost", 5432)

    def detect_mongodb(self) -> bool:
        return self._check_port("localhost", 27017)

    def detect_redis(self) -> bool:
        return self._check_port("localhost", 6379)

    def detect_ollama(self) -> bool:
        # Default Ollama port is 11434
        return self._check_port("localhost", 11434)

    def check_internet_connection(self) -> bool:
        try:
            subprocess.check_call(["ping", "-c", "1", "8.8.8.8"],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
            return True
        except Exception:
            # On Windows 'ping' flags differ; attempt socket-based check
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=1.0)
                return True
            except Exception:
                return False

    def generate_report(self) -> EnvironmentReport:
        report = EnvironmentReport(
            os=self.detect_os(),
            python_version=self.detect_python_version(),
            docker_installed=self.detect_docker(),
            docker_compose_installed=self.detect_docker_compose(),
            postgres_running=self.detect_postgresql(),
            mongodb_running=self.detect_mongodb(),
            redis_running=self.detect_redis(),
            ollama_running=self.detect_ollama(),
            internet=self.check_internet_connection(),
        )
        report.details = {
            "python_executable": sys.executable,
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
    """Guides user through interactive setup process.

    Uses `questionary` for prompts. If questionary is not installed the
    wizard falls back to minimal console prompts.
    """

    def __init__(self):
        if questionary is None:
            print("Warning: 'questionary' not installed. Interactive prompts "
                  "will be basic.")

    def welcome_screen(self, env_report: EnvironmentReport) -> None:
        print("\n🚀 Faceless YouTube Setup Wizard\n===============================\n")
        print("Environment snapshot:")
        print(f"  OS: {env_report.os}")
        print(f"  Python: {env_report.python_version}")
        print(f"  Docker: {'yes' if env_report.docker_installed else 'no'}")
        print(f"  PostgreSQL running locally: {'yes' if env_report.postgres_running else 'no'}")
        print(f"  MongoDB running locally: {'yes' if env_report.mongodb_running else 'no'}")
        print(f"  Redis running locally: {'yes' if env_report.redis_running else 'no'}")
        print("")

    def select_deployment_mode(self) -> str:
        choices = [
            "Docker Full Stack (recommended)",
            "Local Services (advanced)",
            "Hybrid (Docker + local)",
        ]
        if questionary:
            return questionary.select("Select deployment mode:", choices=choices).ask()
        else:
            print("Select deployment mode:")
            for i, c in enumerate(choices, start=1):
                print(f"  {i}. {c}")
            sel = input("Enter choice [1]: ") or "1"
            return choices[int(sel) - 1]

    def configure_docker_mode(self) -> DockerConfig:
        if questionary:
            memory = questionary.text("Memory limit for containers (MB)", default="4096").ask()
            cpu = questionary.text("CPU shares (relative)", default="2").ask()
            api_port = questionary.text("API port (host)", default="8000").ask()
            frontend_port = questionary.text("Frontend port (host)", default="3000").ask()
        else:
            memory = input("Memory limit for containers (MB) [4096]: ") or "4096"
            cpu = input("CPU shares (relative) [2]: ") or "2"
            api_port = input("API port (host) [8000]: ") or "8000"
            frontend_port = input("Frontend port (host) [3000]: ") or "3000"

        return DockerConfig(
            memory_mb=int(memory),
            cpu_shares=int(cpu),
            api_port=int(api_port),
            frontend_port=int(frontend_port),
        )

    def configure_local_mode(self) -> LocalConfig:
        if questionary:
            postgres = questionary.text("Postgres DSN", default="postgresql://user:pass@localhost:5432/faceless").ask()
            mongodb = questionary.text("MongoDB URI", default="mongodb://localhost:27017/faceless").ask()
            redis = questionary.text("Redis URI", default="redis://localhost:6379/0").ask()
        else:
            postgres = input("Postgres DSN [postgresql://user:pass@localhost:5432/faceless]: ") or "postgresql://user:pass@localhost:5432/faceless"
            mongodb = input("MongoDB URI [mongodb://localhost:27017/faceless]: ") or "mongodb://localhost:27017/faceless"
            redis = input("Redis URI [redis://localhost:6379/0]: ") or "redis://localhost:6379/0"

        return LocalConfig(postgres_url=postgres, mongodb_uri=mongodb, redis_url=redis)

    def collect_api_credentials(self) -> Dict[str, str]:
        creds = {}
        if questionary:
            path = questionary.path("Path to YouTube OAuth credentials JSON (optional)").ask()
        else:
            path = input("Path to YouTube OAuth credentials JSON (optional): ")

        if path:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    creds["youtube_credentials_path"] = path
                    creds["youtube_credentials_valid"] = "installed" in data or "web" in data
                except Exception:
                    creds["youtube_credentials_path"] = path
                    creds["youtube_credentials_valid"] = False
            else:
                creds["youtube_credentials_path"] = path
                creds["youtube_credentials_valid"] = False

        return creds

    def verify_configuration(self, config) -> ValidationResult:
        errors: List[str] = []

        # If docker mode: verify docker is installed
        if isinstance(config, DockerConfig):
            if shutil.which("docker") is None:
                errors.append("Docker not found on PATH")

        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def generate_env_file(self, config: Dict[str, str], path: str = ".env") -> None:
        # Basic env file generator — caller provides a mapping
        if os.path.exists(path):
            backup = f"{path}.bak"
            print(f"Backing up existing {path} to {backup}")
            shutil.copy(path, backup)

        with open(path, "w", encoding="utf-8") as fh:
            for k, v in config.items():
                fh.write(f"{k}={v}\n")

    def display_next_steps(self, mode: str) -> None:
        print("\nNext steps:")
        if mode.startswith("Docker"):
            print("  - Start services: docker-compose up -d")
            print("  - Run initial migration: alembic upgrade head")
        else:
            print("  - Start local databases and services as configured")
        print("  - Start the API: uvicorn src.api.main:app --reload")


class ConfigurationManager:
    ENV_TEMPLATE = """
# Generated by setup wizard
# Last updated: {timestamp}

# Database Configuration
DATABASE_URL={DATABASE_URL}
MONGODB_URI={MONGODB_URI}

# Cache Configuration
REDIS_URL={REDIS_URL}

# AI Configuration
OLLAMA_BASE_URL={OLLAMA_BASE_URL}
OLLAMA_MODEL={OLLAMA_MODEL}

# YouTube Configuration
YOUTUBE_OAUTH_CREDENTIALS_PATH={YOUTUBE_OAUTH_CREDENTIALS_PATH}

# Application Configuration
ENVIRONMENT={ENVIRONMENT}
DEBUG={DEBUG}
LOG_LEVEL={LOG_LEVEL}

# Service Ports
API_PORT={API_PORT}
FRONTEND_PORT={FRONTEND_PORT}
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
    try:
        detector = EnvironmentDetector()
        report = detector.generate_report()

        wizard = InteractiveWizard()
        wizard.welcome_screen(report)

        mode = wizard.select_deployment_mode()

        if mode.startswith("Docker"):
            config = wizard.configure_docker_mode()
        elif mode.startswith("Local"):
            config = wizard.configure_local_mode()
        else:
            # Hybrid
            config = wizard.configure_local_mode()

        api_creds = wizard.collect_api_credentials()

        # Build a simple dict for .env
        env_map: Dict[str, str] = {
            "DATABASE_URL": getattr(config, "postgres_url", "postgresql://user:pass@localhost:5432/faceless"),
            "MONGODB_URI": getattr(config, "mongodb_uri", "mongodb://localhost:27017/faceless"),
            "REDIS_URL": getattr(config, "redis_url", "redis://localhost:6379/0"),
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_MODEL": "llama2",
            "YOUTUBE_OAUTH_CREDENTIALS_PATH": api_creds.get("youtube_credentials_path", ""),
            "ENVIRONMENT": "development",
            "DEBUG": "True",
            "LOG_LEVEL": "INFO",
            "API_PORT": str(getattr(config, "api_port", 8000)),
            "FRONTEND_PORT": str(getattr(config, "frontend_port", 3000)),
        }

        cfg_mgr = ConfigurationManager()
        validation = cfg_mgr.validate_configuration(env_map)
        if not validation.passed:
            print("❌ Configuration validation failed:")
            for err in validation.errors:
                print(f"  - {err}")
            return 1

        cfg_mgr.write_env_file(env_map)

        if isinstance(config, DockerConfig):
            docker_helper = DockerSetupHelper()
            override = docker_helper.generate_docker_compose_override(config)
            with open("docker-compose.override.yml", "w", encoding="utf-8") as fh:
                fh.write(override)

        wizard.display_next_steps(mode)

        print("\n✅ Setup wizard completed successfully!")
        return 0
    except KeyboardInterrupt:
        print("\n⚠️ Setup wizard interrupted by user.")
        return 130
    except Exception as e:
        print(f"❌ Error during setup: {str(e)}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
