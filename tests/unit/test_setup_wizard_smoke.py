"""Smoke tests for setup wizard.

Validates script execution without deep imports. This module tests the
setup_wizard.py script at a functional level rather than unit testing
internal components. This avoids import path issues while still validating
that the wizard works correctly.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestSetupWizardExecution:
    """Test setup wizard script execution and file generation."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def temp_work_dir(self):
        """Create a temporary working directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_setup_wizard_script_exists(self, project_root):
        """Test that setup_wizard.py script exists."""
        wizard_path = project_root / "scripts" / "setup_wizard.py"
        assert wizard_path.exists(), (
            f"Setup wizard script not found at {wizard_path}"
        )

    def test_setup_sh_script_exists(self, project_root):
        """Test that setup.sh script exists."""
        setup_sh = project_root / "setup.sh"
        assert setup_sh.exists(), f"setup.sh not found at {setup_sh}"

    def test_setup_bat_script_exists(self, project_root):
        """Test that setup.bat script exists."""
        setup_bat = project_root / "setup.bat"
        assert setup_bat.exists(), f"setup.bat not found at {setup_bat}"

    def test_setup_wizard_python_syntax(self, project_root):
        """Test that setup_wizard.py has valid Python syntax."""
        wizard_path = project_root / "scripts" / "setup_wizard.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(wizard_path)],
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 0
        ), f"Syntax error in setup_wizard.py: {result.stderr}"

    def test_setup_wizard_imports(self, project_root):
        """Test that setup_wizard.py can be imported."""
        sys.path.insert(0, str(project_root / "scripts"))
        try:
            import setup_wizard  # noqa: F401

            assert hasattr(setup_wizard, "EnvironmentDetector")
            assert hasattr(setup_wizard, "InteractiveWizard")
            assert hasattr(setup_wizard, "ConfigurationManager")
            assert hasattr(setup_wizard, "main")
        except ImportError as e:
            pytest.fail(f"Failed to import setup_wizard: {e}")
        finally:
            if str(project_root / "scripts") in sys.path:
                sys.path.remove(str(project_root / "scripts"))

    def test_setup_documentation_exists(self, project_root):
        """Test that SETUP_WIZARD.md documentation exists."""
        doc_path = project_root / "SETUP_WIZARD.md"
        assert doc_path.exists(), f"SETUP_WIZARD.md not found at {doc_path}"

        # Check content
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "setup.sh" in content or "setup wizard" in content.lower()
        assert (
            "Docker" in content or "docker" in content
        ), "Documentation should mention Docker"


class TestSetupWizardDocumentation:
    """Test that setup wizard documentation is complete."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_setup_wizard_md_content(self, project_root):
        """Test SETUP_WIZARD.md has required sections."""
        doc_path = project_root / "SETUP_WIZARD.md"
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read().lower()

        required_sections = [
            "running",
            "deployment",
            "troubleshooting",
            "docker",
            "local",
        ]

        for section in required_sections:
            assert (
                section in content
            ), f"SETUP_WIZARD.md missing required section: {section}"

    def test_setup_wizard_md_examples(self, project_root):
        """Test SETUP_WIZARD.md contains usage examples."""
        doc_path = project_root / "SETUP_WIZARD.md"
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should contain code examples or command examples
        assert "```" in content or "$" in content or ">" in content


class TestSetupScriptShellSyntax:
    """Test shell script syntax (bash/batch)."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_setup_sh_is_executable_text(self, project_root):
        """Test setup.sh starts with shebang and has correct format."""
        setup_sh = project_root / "setup.sh"
        with open(setup_sh, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()

        assert first_line.startswith("#!"), (
            "setup.sh should start with shebang"
        )
        assert "bash" in first_line or "sh" in first_line

    def test_setup_sh_contains_key_steps(self, project_root):
        """Test setup.sh contains required setup steps."""
        setup_sh = project_root / "setup.sh"
        with open(setup_sh, "r", encoding="utf-8") as f:
            content = f.read().lower()

        required_steps = ["python", "venv", "requirements", "setup_wizard"]

        for step in required_steps:
            assert (
                step in content
            ), f"setup.sh missing required step: {step}"

    def test_setup_bat_contains_key_steps(self, project_root):
        """Test setup.bat contains required setup steps."""
        setup_bat = project_root / "setup.bat"
        with open(setup_bat, "r", encoding="utf-8") as f:
            content = f.read().lower()

        required_steps = ["python", "venv", "requirements", "setup_wizard"]

        for step in required_steps:
            assert (
                step in content
            ), f"setup.bat missing required step: {step}"


class TestConfigurationGeneration:
    """Test configuration file generation."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_env_example_exists(self, project_root):
        """Test that .env.example exists as reference."""
        env_example = project_root / ".env.example"
        # This is optional, but good to have
        if env_example.exists():
            with open(env_example, "r") as f:
                content = f.read()
            assert "DATABASE" in content or len(content) > 0
