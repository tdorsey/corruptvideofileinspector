"""
Test GitHub Actions workflow files for syntax and structure validation.
"""

import unittest
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit


class TestGitHubWorkflows(unittest.TestCase):
    """Test GitHub Actions workflow files"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.repo_root = Path(__file__).parent.parent.parent
        self.workflows_dir = self.repo_root / ".github" / "workflows"

    def test_auto_create_branch_workflow_exists(self):
        """Test that auto-create-branch workflow file exists"""
        workflow_file = self.workflows_dir / "auto-create-branch.yml"
        assert workflow_file.exists(), "auto-create-branch.yml workflow file should exist"

    def test_auto_create_branch_workflow_valid_yaml(self):
        """Test that auto-create-branch workflow has valid YAML syntax"""
        workflow_file = self.workflows_dir / "auto-create-branch.yml"

        with open(workflow_file) as f:
            try:
                workflow_data = yaml.safe_load(f)
                assert isinstance(workflow_data, dict), "Workflow should be a valid YAML dictionary"
            except yaml.YAMLError as e:
                self.fail(f"Workflow YAML is invalid: {e}")

    def test_auto_create_branch_workflow_structure(self):
        """Test that auto-create-branch workflow has required structure"""
        workflow_file = self.workflows_dir / "auto-create-branch.yml"

        with open(workflow_file) as f:
            workflow_data = yaml.safe_load(f)

        # Test required top-level keys
        assert "name" in workflow_data, "Workflow should have a name"
        assert "on" in workflow_data, "Workflow should have trigger conditions"
        assert "permissions" in workflow_data, "Workflow should define permissions"
        assert "jobs" in workflow_data, "Workflow should have jobs"

        # Test specific trigger
        assert "issues" in workflow_data["on"], "Workflow should trigger on issues"
        assert "opened" in workflow_data["on"]["issues"]["types"], "Workflow should trigger on issue opened"

        # Test permissions
        permissions = workflow_data["permissions"]
        assert "contents" in permissions, "Workflow should have contents permission"
        assert "issues" in permissions, "Workflow should have issues permission"
        assert permissions["contents"] == "write", "Contents permission should be write"
        assert permissions["issues"] == "write", "Issues permission should be write"

        # Test job structure
        jobs = workflow_data["jobs"]
        assert "create-branch" in jobs, "Workflow should have create-branch job"

        create_branch_job = jobs["create-branch"]
        assert "runs-on" in create_branch_job, "Job should specify runner"
        assert "steps" in create_branch_job, "Job should have steps"

        # Test that job uses actions/github-script
        steps = create_branch_job["steps"]
        github_script_step = None
        for step in steps:
            if step.get("uses", "").startswith("actions/github-script"):
                github_script_step = step
                break

        assert github_script_step is not None, "Job should use actions/github-script action"
        assert "script" in github_script_step["with"], "github-script step should have script"

    def test_workflow_names_are_unique(self):
        """Test that all workflow files have unique names"""
        workflow_names = set()

        for workflow_file in self.workflows_dir.glob("*.yml"):
            with open(workflow_file) as f:
                workflow_data = yaml.safe_load(f)
                name = workflow_data.get("name", "")

                assert name not in workflow_names, f"Workflow name '{name}' is duplicated across workflow files"
                workflow_names.add(name)

    def test_all_workflows_valid_yaml(self):
        """Test that all workflow files have valid YAML syntax"""
        for workflow_file in self.workflows_dir.glob("*.yml"):
            with open(workflow_file) as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    self.fail(f"Workflow {workflow_file.name} has invalid YAML: {e}")


if __name__ == "__main__":
    unittest.main()
