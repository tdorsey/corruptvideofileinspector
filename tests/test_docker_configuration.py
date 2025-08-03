"""Tests for Docker Compose configuration files."""

import unittest
from pathlib import Path


class TestDockerComposeConfiguration(unittest.TestCase):
    """Test Docker Compose configuration for correct command format."""

    def test_docker_compose_yml_trakt_command_format(self) -> None:
        """Test that docker-compose.yml trakt service uses correct command format."""
        docker_compose_path = Path(__file__).parent.parent / "docker" / "docker-compose.yml"

        if not docker_compose_path.exists():
            self.skipTest("docker-compose.yml not found")

        with docker_compose_path.open("r", encoding="utf-8") as f:
            content = f.read()

        # Check that trakt service exists
        assert "trakt:" in content, "Should contain trakt service definition"
        assert "sync" in content, "Should contain sync command"

        # Find the trakt service section and verify it uses positional argument format
        lines = content.split("\n")
        in_trakt_service = False
        trakt_command_lines = []

        for line in lines:
            if line.strip().startswith("trakt:"):
                in_trakt_service = True
                continue
            if in_trakt_service and line.strip() and not line.startswith("  "):
                # End of trakt service section
                break
            if in_trakt_service and ("command:" in line or line.strip().startswith("- ")):
                trakt_command_lines.append(line.strip())

        # Verify the command format
        command_content = " ".join(trakt_command_lines)

        # Should use positional argument format
        assert (
            "/app/output/scan_results.json" in command_content
        ), "Trakt command should specify scan results file path"

        # Should NOT use --scan-file option format in trakt service
        for line in trakt_command_lines:
            if "--scan-file" in line:
                raise AssertionError(f"Trakt service should not use --scan-file option: {line}")

    def test_docker_compose_dev_yml_trakt_command_format(self) -> None:
        """Test that docker-compose.dev.yml trakt service uses correct command format."""
        docker_compose_dev_path = Path(__file__).parent.parent / "docker" / "docker-compose.dev.yml"

        if not docker_compose_dev_path.exists():
            self.skipTest("docker-compose.dev.yml not found")

        with docker_compose_dev_path.open("r", encoding="utf-8") as f:
            content = f.read()

        # Check if trakt-dev service exists
        if "trakt-dev:" not in content:
            self.skipTest("trakt-dev service not found in docker-compose.dev.yml")

        # Should use positional argument format
        assert (
            "/app/output/scan_results.json" in content
        ), "Trakt-dev command should specify scan results file path"

        # Should NOT use --scan-file option format anywhere in trakt-dev
        lines = content.split("\n")
        in_trakt_dev_service = False

        for line in lines:
            if line.strip().startswith("trakt-dev:"):
                in_trakt_dev_service = True
                continue
            if in_trakt_dev_service and line.strip() and not line.startswith("  "):
                # End of trakt-dev service section
                break
            if in_trakt_dev_service and "--scan-file" in line:
                raise AssertionError(
                    f"Trakt-dev service should not use --scan-file option: {line.strip()}"
                )

    def test_report_service_can_use_scan_file_option(self) -> None:
        """Test that report service correctly uses --scan-file option (this is valid)."""
        docker_compose_path = Path(__file__).parent.parent / "docker" / "docker-compose.yml"

        if not docker_compose_path.exists():
            self.skipTest("docker-compose.yml not found")

        with docker_compose_path.open("r", encoding="utf-8") as f:
            content = f.read()

        # The report service should use --scan-file option (this is correct behavior)
        if "report:" in content:
            assert "--scan-file" in content, "Report service should use --scan-file option"


if __name__ == "__main__":
    unittest.main()
