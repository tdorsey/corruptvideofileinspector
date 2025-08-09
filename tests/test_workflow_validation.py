# Test for actionlint validation
import yaml
import subprocess
import tempfile
import os
import pytest


def test_actionlint_validation():
    """Test that actionlint properly validates GitHub Action workflows."""
    
    # Valid workflow content
    valid_workflow = """
name: Test Workflow
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test step
        run: echo "Hello World"
"""

    # Invalid workflow content (missing 'on' field)
    invalid_workflow = """
name: Test Workflow
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test step
        run: echo "Hello World"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        try:
            # Test valid workflow
            f.write(valid_workflow)
            f.flush()
            
            # Check if actionlint is available
            try:
                result = subprocess.run(['/tmp/actionlint', f.name], 
                                      capture_output=True, text=True)
                # Valid workflow should pass (exit code 0)
                assert result.returncode == 0, f"Valid workflow failed: {result.stderr}"
            except FileNotFoundError:
                pytest.skip("actionlint not available for testing")
            
            # Test invalid workflow
            f.seek(0)
            f.truncate()
            f.write(invalid_workflow)
            f.flush()
            
            result = subprocess.run(['/tmp/actionlint', f.name], 
                                  capture_output=True, text=True)
            # Invalid workflow should fail (non-zero exit code)
            assert result.returncode != 0, "Invalid workflow should have failed validation"
            
        finally:
            os.unlink(f.name)


def test_workflow_yaml_syntax():
    """Test that our workflow validation file has valid YAML syntax."""
    workflow_file = '.github/workflows/workflow-validation.yml'
    
    if os.path.exists(workflow_file):
        with open(workflow_file, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Workflow file has invalid YAML syntax: {e}")
    else:
        pytest.skip("Workflow validation file not found")


def test_existing_workflows_syntax():
    """Test that all existing workflow files have valid YAML syntax."""
    workflows_dir = '.github/workflows'
    
    if not os.path.exists(workflows_dir):
        pytest.skip("Workflows directory not found")
    
    for filename in os.listdir(workflows_dir):
        if filename.endswith(('.yml', '.yaml')):
            filepath = os.path.join(workflows_dir, filename)
            with open(filepath, 'r') as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Workflow file {filename} has invalid YAML syntax: {e}")