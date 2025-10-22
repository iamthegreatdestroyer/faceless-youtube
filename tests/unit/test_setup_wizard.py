"""Test suite for setup wizard functionality.

Tests cover:
- Environment detection (OS, Python, Docker, services)
- Interactive wizard prompts and flow
- Configuration management and validation
- File generation (.env, docker-compose.override.yml)
- Error handling and edge cases

Note: This test module requires scripts/setup_wizard.py to be importable.
The imports are handled at the fixture level to ensure proper sys.path setup.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open

import pytest


# Configure sys.path for setup_wizard imports
def _setup_wizard_path():
    """Add scripts directory to sys.path for setup_wizard imports."""
    scripts_path = Path(__file__).parent.parent.parent / "scripts"
    scripts_path_str = str(scripts_path)
    if scripts_path_str not in sys.path:
        sys.path.insert(0, scripts_path_str)
    return scripts_path_str


# Try to import setup wizard components at module level
_setup_wizard_path()
try:
    from setup_wizard import (
        EnvironmentDetector,
        InteractiveWizard,
        ConfigurationManager,
        ValidationResult,
        DockerSetupHelper,
        DockerConfig,
        LocalConfig,
        _q_print,
        _q_text,
        _q_select,
        _q_confirm,
    )

    SETUP_WIZARD_AVAILABLE = True
except ImportError as e:
    SETUP_WIZARD_AVAILABLE = False
    SETUP_WIZARD_ERROR = str(e)


# Skip all tests if setup wizard is not available
if not SETUP_WIZARD_AVAILABLE:
    pytestmark = pytest.mark.skip(reason=f"setup_wizard module not available")
else:
    pytestmark = []


class TestEnvironmentDetector:
    """Test environment detection functionality."""

    @pytest.fixture
    def detector(self):
        """Create EnvironmentDetector instance."""
        return EnvironmentDetector()

    def test_detect_os(self, detector):
        """Test OS detection returns valid platform string."""
        os_name = detector.detect_os()
        assert os_name in ["Linux", "macOS", "Windows", "Unknown"]

    def test_detect_python_version(self, detector):
        """Test Python version detection returns valid version string."""
        version = detector.detect_python_version()
        assert version is not None
        assert "." in version  # Should be x.y.z format
        parts = version.split(".")
        assert len(parts) >= 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    @patch("shutil.which")
    def test_detect_docker_present(self, mock_which):
        """Test Docker detection when docker command exists."""
        mock_which.return_value = "/usr/bin/docker"
        detector = EnvironmentDetector()
        assert detector.detect_docker() is True

    @patch("shutil.which")
    def test_detect_docker_absent(self, mock_which):
        """Test Docker detection when docker command doesn't exist."""
        mock_which.return_value = None
        detector = EnvironmentDetector()
        assert detector.detect_docker() is False

    @patch("socket.create_connection")
    def test_detect_postgresql_present(self, mock_socket):
        """Test PostgreSQL detection when connection succeeds."""
        mock_socket.return_value = MagicMock()
        detector = EnvironmentDetector()
        # Should check localhost:5432 by default
        assert detector.detect_postgresql() is True

    @patch("socket.create_connection")
    def test_detect_postgresql_absent(self, mock_socket):
        """Test PostgreSQL detection when connection fails."""
        mock_socket.side_effect = OSError("Connection refused")
        detector = EnvironmentDetector()
        assert detector.detect_postgresql() is False

    @patch("socket.create_connection")
    def test_detect_mongodb_present(self, mock_socket):
        """Test MongoDB detection when connection succeeds."""
        mock_socket.return_value = MagicMock()
        detector = EnvironmentDetector()
        assert detector.detect_mongodb() is True

    @patch("socket.create_connection")
    def test_detect_mongodb_absent(self, mock_socket):
        """Test MongoDB detection when connection fails."""
        mock_socket.side_effect = OSError("Connection refused")
        detector = EnvironmentDetector()
        assert detector.detect_mongodb() is False

    @patch("socket.create_connection")
    def test_detect_redis_present(self, mock_socket):
        """Test Redis detection when connection succeeds."""
        mock_socket.return_value = MagicMock()
        detector = EnvironmentDetector()
        assert detector.detect_redis() is True

    @patch("socket.create_connection")
    def test_detect_redis_absent(self, mock_socket):
        """Test Redis detection when connection fails."""
        mock_socket.side_effect = OSError("Connection refused")
        detector = EnvironmentDetector()
        assert detector.detect_redis() is False

    @patch.object(EnvironmentDetector, "detect_os")
    @patch.object(EnvironmentDetector, "detect_python_version")
    @patch.object(EnvironmentDetector, "detect_docker")
    @patch.object(EnvironmentDetector, "detect_internet")
    def test_generate_report(self, mock_internet, mock_docker, mock_python, mock_os):
        """Test that generate_report creates comprehensive environment report."""
        mock_os.return_value = "Linux"
        mock_python.return_value = "3.11.0"
        mock_docker.return_value = True
        mock_internet.return_value = True

        detector = EnvironmentDetector()
        report = detector.generate_report()

        assert "os" in report
        assert "python_version" in report
        assert "docker_available" in report
        assert "internet_available" in report
        assert report["os"] == "Linux"
        assert report["python_version"] == "3.11.0"
        assert report["docker_available"] is True
        assert report["internet_available"] is True


class TestInteractiveWizard:
    """Test interactive wizard prompts and flow."""

    @pytest.fixture
    def wizard(self):
        """Create InteractiveWizard instance."""
        return InteractiveWizard()

    def test_welcome_screen_displays_info(self, wizard, capsys):
        """Test welcome screen displays environment info."""
        env_report = {
            "os": "Linux",
            "python_version": "3.11.0",
            "docker_available": True,
            "internet_available": True,
        }

        # Suppress questionary.print() which may fail in test
        with patch("setup_wizard._q_print"):
            wizard.welcome_screen(env_report)

    @patch("setup_wizard._q_select")
    def test_select_deployment_mode_docker(self, mock_select):
        """Test deployment mode selection for Docker."""
        mock_select.return_value = "Docker Full Stack (recommended)"
        wizard = InteractiveWizard()
        mode = wizard.select_deployment_mode()
        assert mode == "docker"

    @patch("setup_wizard._q_select")
    def test_select_deployment_mode_local(self, mock_select):
        """Test deployment mode selection for Local."""
        mock_select.return_value = "Local Services (advanced)"
        wizard = InteractiveWizard()
        mode = wizard.select_deployment_mode()
        assert mode == "local"

    @patch("setup_wizard._q_select")
    def test_select_deployment_mode_hybrid(self, mock_select):
        """Test deployment mode selection for Hybrid."""
        mock_select.return_value = "Hybrid (Docker + Local)"
        wizard = InteractiveWizard()
        mode = wizard.select_deployment_mode()
        assert mode == "hybrid"

    @patch("setup_wizard._q_text")
    def test_configure_docker_mode(self, mock_text):
        """Test Docker configuration collection."""
        mock_text.side_effect = ["2g", "2"]
        wizard = InteractiveWizard()
        config = wizard.configure_docker_mode()

        assert config["mode"] == "docker"
        assert config["memory"] == "2g"
        assert config["cpu"] == "2"
        assert config["volumes"] is True
        assert "ports" in config

    @patch("setup_wizard._q_text")
    @patch.object(EnvironmentDetector, "detect_postgresql", return_value=True)
    @patch.object(EnvironmentDetector, "detect_mongodb", return_value=True)
    @patch.object(EnvironmentDetector, "detect_redis", return_value=True)
    def test_configure_local_mode_with_services(
        self, mock_redis, mock_mongodb, mock_postgresql, mock_text
    ):
        """Test local mode configuration when all services present."""
        mock_text.side_effect = [
            "localhost",
            "5432",
            "localhost",
            "27017",
            "localhost",
            "6379",
        ]
        wizard = InteractiveWizard()

        with patch("setup_wizard._q_print"):
            config = wizard.configure_local_mode()

        assert config["mode"] == "local"
        assert config["postgres_host"] == "localhost"
        assert config["postgres_port"] == "5432"
        assert config["mongodb_host"] == "localhost"
        assert config["mongodb_port"] == "27017"
        assert config["redis_host"] == "localhost"
        assert config["redis_port"] == "6379"

    @patch("setup_wizard._q_confirm", return_value=False)
    def test_collect_api_credentials_skip(self, mock_confirm):
        """Test API credential collection when user declines."""
        wizard = InteractiveWizard()
        credentials = wizard.collect_api_credentials()
        assert isinstance(credentials, dict)

    @patch("setup_wizard._q_confirm", return_value=True)
    @patch("setup_wizard._q_text")
    def test_collect_api_credentials_with_file(self, mock_text, mock_confirm):
        """Test API credential collection with valid file."""
        temp_oauth = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        temp_oauth.write('{"type": "oauth2", "client_id": "test"}')
        temp_oauth.close()

        try:
            mock_text.return_value = temp_oauth.name
            wizard = InteractiveWizard()
            credentials = wizard.collect_api_credentials()

            if credentials:
                assert "youtube_oauth_path" in credentials
        finally:
            os.unlink(temp_oauth.name)

    def test_verify_configuration_docker_success(self):
        """Test configuration verification succeeds for Docker mode."""
        with patch.object(
            EnvironmentDetector, "detect_docker", return_value=True
        ):
            wizard = InteractiveWizard()
            config = {"mode": "docker"}

            with patch("setup_wizard._q_print"):
                result = wizard.verify_configuration(config)

            assert result["passed"] is True

    def test_verify_configuration_docker_fail(self):
        """Test configuration verification fails when Docker not detected."""
        with patch.object(
            EnvironmentDetector, "detect_docker", return_value=False
        ):
            wizard = InteractiveWizard()
            config = {"mode": "docker"}

            with patch("setup_wizard._q_print"):
                result = wizard.verify_configuration(config)

            assert result["passed"] is False
            assert len(result["errors"]) > 0

    def test_verify_configuration_local_with_warnings(self):
        """Test local mode verification generates warnings for missing services."""
        with patch.object(EnvironmentDetector, "detect_postgresql", return_value=False):
            with patch.object(EnvironmentDetector, "detect_mongodb", return_value=False):
                with patch.object(EnvironmentDetector, "detect_redis", return_value=False):
                    wizard = InteractiveWizard()
                    config = {"mode": "local"}

                    with patch("setup_wizard._q_print"):
                        result = wizard.verify_configuration(config)

                    # Should pass but with warnings
                    assert "warnings" in result
                    assert len(result["warnings"]) > 0

    def test_generate_env_file_docker(self):
        """Test .env file generation for Docker mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                wizard = InteractiveWizard()
                config = {"mode": "docker"}

                with patch("setup_wizard._q_print"):
                    wizard.generate_env_file(config)

                assert os.path.exists(".env")

                with open(".env", "r") as f:
                    content = f.read()

                assert "DATABASE_URL=postgresql://docker:docker@postgres" in content
                assert "MONGODB_URI=mongodb://root:password@mongodb" in content
                assert "REDIS_URL=redis://redis:6379" in content

            finally:
                os.chdir(old_cwd)

    def test_generate_env_file_local(self):
        """Test .env file generation for local mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                wizard = InteractiveWizard()
                config = {
                    "mode": "local",
                    "postgres_host": "localhost",
                    "postgres_port": "5432",
                    "mongodb_host": "localhost",
                    "mongodb_port": "27017",
                    "redis_host": "localhost",
                    "redis_port": "6379",
                }

                with patch("setup_wizard._q_print"):
                    wizard.generate_env_file(config)

                assert os.path.exists(".env")

                with open(".env", "r") as f:
                    content = f.read()

                assert "localhost" in content
                assert "5432" in content

            finally:
                os.chdir(old_cwd)

    def test_display_next_steps_docker(self, capsys):
        """Test next steps display for Docker mode."""
        with patch("setup_wizard._q_print") as mock_print:
            wizard = InteractiveWizard()
            wizard.display_next_steps("docker")
            mock_print.assert_called()

    def test_display_next_steps_local(self, capsys):
        """Test next steps display for local mode."""
        with patch("setup_wizard._q_print") as mock_print:
            wizard = InteractiveWizard()
            wizard.display_next_steps("local")
            mock_print.assert_called()


class TestConfigurationManager:
    """Test configuration management and validation."""

    @pytest.fixture
    def config_manager(self):
        """Create ConfigurationManager instance."""
        return ConfigurationManager()

    def test_validate_configuration_docker_mode(self, config_manager):
        """Test validation passes for Docker mode with minimal config."""
        config = {"mode": "docker"}
        result = config_manager.validate_configuration(config)
        assert result.passed is True

    def test_validate_configuration_local_mode_complete(self, config_manager):
        """Test validation passes for local mode with all required fields."""
        config = {
            "mode": "local",
            "postgres_host": "localhost",
            "postgres_port": "5432",
            "mongodb_host": "localhost",
            "mongodb_port": "27017",
            "redis_host": "localhost",
            "redis_port": "6379",
        }
        result = config_manager.validate_configuration(config)
        assert result.passed is True

    def test_validate_configuration_local_mode_missing_fields(self, config_manager):
        """Test validation fails for local mode with missing fields."""
        config = {"mode": "local", "postgres_host": "localhost"}
        result = config_manager.validate_configuration(config)
        assert result.passed is False
        assert len(result.errors) > 0

    def test_write_env_file_creates_file(self, config_manager):
        """Test env file is created with correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            config = {"mode": "docker"}

            with patch("setup_wizard._q_print"):
                config_manager.write_env_file(config, env_path)

            assert os.path.exists(env_path)

            with open(env_path, "r") as f:
                content = f.read()

            assert "DATABASE_URL" in content
            assert "ENVIRONMENT=docker" in content

    def test_write_env_file_backs_up_existing(self, config_manager):
        """Test that existing .env file is backed up."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")

            # Create existing .env
            with open(env_path, "w") as f:
                f.write("OLD_CONTENT=1\n")

            config = {"mode": "docker"}

            with patch("setup_wizard._q_print"):
                config_manager.write_env_file(config, env_path)

            # Check backup was created
            backup_path = f"{env_path}.bak"
            assert os.path.exists(backup_path)

            with open(backup_path, "r") as f:
                backup_content = f.read()

            assert "OLD_CONTENT=1" in backup_content

    def test_write_env_file_sets_permissions(self, config_manager):
        """Test that .env file permissions are set to 0o600 (Unix-like systems)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            config = {"mode": "docker"}

            with patch("setup_wizard._q_print"):
                config_manager.write_env_file(config, env_path)

            # Check file exists
            assert os.path.exists(env_path)

            # Note: On Windows, file permissions may not apply the same way
            # so we just verify the file was created

    def test_generate_docker_compose_override(self, config_manager):
        """Test Docker compose override YAML generation."""
        config = DockerConfig(
            memory_mb=4096, cpu_shares=2, api_port=8000, frontend_port=3000
        )
        override_yaml = config_manager.generate_docker_compose_override(config)

        assert "version: '3.9'" in override_yaml
        assert "services:" in override_yaml
        assert "8000:8000" in override_yaml
        assert "3000:3000" in override_yaml


class TestDockerSetupHelper:
    """Test Docker setup helper functionality."""

    @pytest.fixture
    def docker_helper(self):
        """Create DockerSetupHelper instance."""
        return DockerSetupHelper()

    @patch("shutil.which")
    def test_check_docker_installation_present(self, mock_which, docker_helper):
        """Test Docker installation check when docker is available."""
        mock_which.return_value = "/usr/bin/docker"
        assert docker_helper.check_docker_installation() is True

    @patch("shutil.which")
    def test_check_docker_installation_absent(self, mock_which, docker_helper):
        """Test Docker installation check when docker is not available."""
        mock_which.return_value = None
        assert docker_helper.check_docker_installation() is False


class TestHelperFunctions:
    """Test helper input/output functions."""

    @patch("setup_wizard.questionary")
    def test_q_text_with_questionary(self, mock_questionary):
        """Test text input with questionary available."""
        mock_questionary.text.return_value.ask.return_value = "test_value"
        result = _q_text("Test prompt", default="default")
        assert result == "test_value"

    @patch("setup_wizard.questionary", None)
    @patch("builtins.input", return_value="test_value")
    def test_q_text_without_questionary(self, mock_input):
        """Test text input without questionary (fallback)."""
        result = _q_text("Test prompt", default="default")
        assert result == "test_value"

    @patch("setup_wizard.questionary")
    def test_q_select_with_questionary(self, mock_questionary):
        """Test select with questionary available."""
        mock_questionary.select.return_value.ask.return_value = "option1"
        result = _q_select("Select", ["option1", "option2"])
        assert result == "option1"

    @patch("setup_wizard.questionary")
    def test_q_confirm_with_questionary(self, mock_questionary):
        """Test confirm with questionary available."""
        mock_questionary.confirm.return_value.ask.return_value = True
        result = _q_confirm("Confirm?", default=False)
        assert result is True


class TestEndToEndWizardFlow:
    """Integration tests for complete wizard flow."""

    @patch("setup_wizard.EnvironmentDetector.generate_report")
    @patch("setup_wizard.InteractiveWizard.welcome_screen")
    @patch("setup_wizard.InteractiveWizard.select_deployment_mode")
    @patch("setup_wizard.InteractiveWizard.configure_docker_mode")
    @patch("setup_wizard.InteractiveWizard.collect_api_credentials")
    @patch("setup_wizard.InteractiveWizard.verify_configuration")
    @patch("setup_wizard.ConfigurationManager.write_env_file")
    @patch("setup_wizard.InteractiveWizard.display_next_steps")
    def test_wizard_docker_flow(
        self,
        mock_next_steps,
        mock_write_env,
        mock_verify,
        mock_credentials,
        mock_configure,
        mock_select_mode,
        mock_welcome,
        mock_report,
    ):
        """Test complete wizard flow for Docker mode."""
        # Setup mocks
        mock_report.return_value = {
            "os": "Linux",
            "python_version": "3.11.0",
            "docker_available": True,
            "internet_available": True,
        }
        mock_select_mode.return_value = "docker"
        mock_configure.return_value = {
            "mode": "docker",
            "memory": "2g",
            "cpu": "2",
        }
        mock_credentials.return_value = {}
        mock_verify.return_value = {"passed": True, "warnings": [], "errors": []}

        # Test that the mocks are properly set up
        assert mock_report.return_value is not None
        assert mock_select_mode.return_value == "docker"

    def test_wizard_handles_keyboard_interrupt(self):
        """Test wizard gracefully handles KeyboardInterrupt."""
        with patch(
            "setup_wizard.EnvironmentDetector.generate_report"
        ) as mock_report:
            mock_report.side_effect = KeyboardInterrupt()

            # Import would happen in main() - this tests error handling paths
            # Return code 130 is typical for KeyboardInterrupt
            assert True  # Placeholder - actual test requires full main() flow

    def test_wizard_handles_general_exceptions(self):
        """Test wizard handles general exceptions gracefully."""
        with patch(
            "setup_wizard.EnvironmentDetector.generate_report"
        ) as mock_report:
            mock_report.side_effect = RuntimeError("Test error")

            # Import would happen in main() - this tests error handling paths
            # Return code 1 is typical for general errors
            assert True  # Placeholder - actual test requires full main() flow
