#!/usr/bin/env python3
"""
Simple script to test basic code quality manually.
This checks for obvious issues without requiring external tools.
"""

import ast
import logging
from pathlib import Path

# Configure logging for development check utility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def check_python_syntax(file_path):
    """Check if a Python file has valid syntax."""
    logger.debug(f"Checking syntax for {file_path}")
    try:
        with open(file_path, encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        logger.debug(f"Syntax check passed for {file_path}")
        return True, None
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error checking syntax for {file_path}: {e}")
        return False, str(e)


def check_line_length(file_path, max_length=100):
    """Check for lines that are too long."""
    issues = []
    try:
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if len(line.rstrip()) > max_length:
                    issues.append(f"Line {line_num}: {len(line.rstrip())} chars")
    except Exception as e:
        issues.append(f"Error reading file: {e}")
    return issues


def check_basic_imports(file_path):
    """Check for potential import issues."""
    issues = []
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Parse the AST to find imports
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("."):
                        issues.append(f"Relative import: {alias.name}")
    except Exception as e:
        issues.append(f"Error parsing imports: {e}")
    return issues


def main():
    """Run basic code quality checks."""
    logger.info("Starting basic code quality checks")
    print("Running basic code quality checks...")
    print("=" * 50)

    py_files = list(Path().glob("*.py"))
    if not py_files:
        logger.warning("No Python files found in current directory")
        print("No Python files found in current directory")
        return

    logger.info(f"Found {len(py_files)} Python files to check")
    all_good = True

    for py_file in py_files:
        logger.debug(f"Checking file: {py_file}")
        print(f"\nChecking {py_file}:")

        # Syntax check
        syntax_ok, syntax_error = check_python_syntax(py_file)
        if syntax_ok:
            print("  ✓ Syntax valid")
        else:
            print(f"  ✗ Syntax error: {syntax_error}")
            all_good = False

        # Line length check
        long_lines = check_line_length(py_file)
        if not long_lines:
            print("  ✓ Line lengths OK")
        else:
            print("  ⚠ Long lines found:")
            for line in long_lines[:3]:  # Show first 3
                print(f"    {line}")
            if len(long_lines) > 3:
                print(f"    ... and {len(long_lines) - 3} more")

        # Import check
        import_issues = check_basic_imports(py_file)
        if not import_issues:
            print("  ✓ Imports look good")
        else:
            print("  ⚠ Import issues:")
            for issue in import_issues:
                print(f"    {issue}")

    print("\n" + "=" * 50)
    if all_good:
        logger.info("All basic checks passed")
        print("✓ Basic checks passed!")
    else:
        logger.warning("Some issues found during basic checks")
        print("⚠ Some issues found - consider running proper linting tools")

    logger.info("Development check completed")
    print("\nTo install proper development tools:")
    print("  pip install -e '.[dev]'")
    print("\nThen run:")
    print("  make check  # or black . && ruff check . && mypy .")


if __name__ == "__main__":
    main()
