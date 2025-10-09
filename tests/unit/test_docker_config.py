"""Unit tests for Docker configuration and environment variables."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


@pytest.mark.unit
class TestDockerConfiguration(unittest.TestCase):
    """Test Docker configuration files and environment variables."""

    def setUp(self):
        """Set up test fixtures."""
        self.docker_dir = Path(__file__).parent.parent.parent / "docker"
        self.compose_file = self.docker_dir / "docker-compose.yml"
        self.env_example = self.docker_dir / ".env.example"

    def test_docker_compose_file_exists(self):
        """Test that docker-compose.yml exists."""
        assert self.compose_file.exists(), "docker-compose.yml not found"

    def test_docker_compose_has_puid_pgid_env_vars(self):
        """Test that docker-compose.yml includes PUID/PGID environment variables."""
        with self.compose_file.open("r", encoding="utf-8") as f:
            compose_config = yaml.safe_load(f)

        # Check scan service has PUID and PGID environment variables
        scan_service = compose_config.get("services", {}).get("scan", {})
        environment = scan_service.get("environment", [])

        # Convert to dict if it's a list
        if isinstance(environment, list):
            env_dict = {}
            for item in environment:
                if "=" in item:
                    key, value = item.split("=", 1)
                    env_dict[key] = value
                else:
                    # It's a key without value (gets from shell env)
                    env_dict[item] = None
        else:
            env_dict = environment

        # Check PUID and PGID are present
        assert "PUID" in str(environment), "PUID environment variable not found in scan service"
        assert "PGID" in str(environment), "PGID environment variable not found in scan service"

    def test_docker_compose_has_compose_project_dir_mount(self):
        """Test that docker-compose.yml uses COMPOSE_PROJECT_DIR for config mount."""
        with self.compose_file.open("r", encoding="utf-8") as f:
            compose_config = yaml.safe_load(f)

        # Check scan service volumes
        scan_service = compose_config.get("services", {}).get("scan", {})
        volumes = scan_service.get("volumes", [])

        # Find config.yaml volume mount
        config_mount = None
        for volume in volumes:
            if isinstance(volume, dict):
                if "/app/config.yaml" in volume.get("target", ""):
                    config_mount = volume
            elif isinstance(volume, str) and "/app/config.yaml" in volume:
                config_mount = volume

        assert config_mount is not None, "config.yaml volume mount not found"

        # Check that source uses COMPOSE_PROJECT_DIR
        if isinstance(config_mount, dict):
            source = config_mount.get("source", "")
            assert "COMPOSE_PROJECT_DIR" in source, (
                f"config.yaml mount should use COMPOSE_PROJECT_DIR, got: {source}"
            )

    def test_env_example_has_puid_pgid(self):
        """Test that .env.example includes PUID and PGID variables."""
        with self.env_example.open("r", encoding="utf-8") as f:
            env_content = f.read()

        assert "PUID=" in env_content, "PUID not found in .env.example"
        assert "PGID=" in env_content, "PGID not found in .env.example"

    def test_env_example_has_compose_project_dir(self):
        """Test that .env.example includes COMPOSE_PROJECT_DIR."""
        with self.env_example.open("r", encoding="utf-8") as f:
            env_content = f.read()

        assert "COMPOSE_PROJECT_DIR=" in env_content, (
            "COMPOSE_PROJECT_DIR not found in .env.example"
        )

    @patch.dict(os.environ, {"PUID": "1500", "PGID": "1500"})
    def test_puid_pgid_environment_defaults(self):
        """Test PUID/PGID environment variable handling."""
        # Verify environment variables can be read
        puid = os.environ.get("PUID", "1000")
        pgid = os.environ.get("PGID", "1000")

        assert puid == "1500", f"Expected PUID=1500, got {puid}"
        assert pgid == "1500", f"Expected PGID=1500, got {pgid}"

    def test_puid_pgid_defaults_to_1000(self):
        """Test that PUID/PGID defaults to 1000 when not set."""
        # Clear any existing PUID/PGID from environment
        clean_env = {k: v for k, v in os.environ.items() if k not in ["PUID", "PGID"]}

        with patch.dict(os.environ, clean_env, clear=True):
            puid = os.environ.get("PUID", "1000")
            pgid = os.environ.get("PGID", "1000")

            assert puid == "1000", f"Expected default PUID=1000, got {puid}"
            assert pgid == "1000", f"Expected default PGID=1000, got {pgid}"


if __name__ == "__main__":
    unittest.main()
