#!/usr/bin/env python3
"""
Tests for GitHub workflow logic for issue reference detection.

This test validates that the workflow logic correctly detects issue references
in PR titles, bodies, and branch names, particularly addressing the bug where
issue references in PR bodies were not being detected.
"""

import re
import unittest


class TestWorkflowIssueDetection(unittest.TestCase):
    """Test workflow logic for detecting issue references in PRs"""

    def setUp(self):
        """Set up the patterns used in the workflow"""
        self.issue_ref_pattern = re.compile(r'#(\d+)')
        self.branch_issue_pattern = re.compile(r'(?:issue-|fix-|feature-|bug-|hotfix-)(\d+)', re.IGNORECASE)

    def detect_issue_reference(self, title, body, branch_name):
        """
        Replicate the workflow logic for detecting issue references.
        This matches the logic in .github/workflows/ci.yml
        """
        # Try title first
        match = self.issue_ref_pattern.search(title)
        if match:
            return match.group(1), 'title'
            
        # Try body
        if body:
            match = self.issue_ref_pattern.search(body)
            if match:
                return match.group(1), 'body'
                
        # Try branch name (direct reference)
        match = self.issue_ref_pattern.search(branch_name)
        if match:
            return match.group(1), 'branch (direct)'
        
        # Try branch name (pattern)
        match = self.branch_issue_pattern.search(branch_name)
        if match:
            return match.group(1), 'branch (pattern)'
            
        return None, None

    def test_pr_175_scenario(self):
        """Test the scenario from PR #175 that failed in the original workflow"""
        title = 'feat(cli): restore JSON output support while maintaining database-first architecture'
        body = '''This PR restores JSON file output capabilities while maintaining the database-driven architecture as the primary storage mechanism.

## Key Changes

**Database Storage (Primary & Default)**:
- All scan and probe results automatically stored in SQLite database
- Database storage enabled by default with `--database` flag
- Advanced querying capabilities via `database query` commands
- Maintains all existing database functionality and performance benefits

**JSON File Output (Secondary & Optional)**:
- Restored `--output`, `--format`, `--pretty` CLI options to scan command
- Added file output support to list-files command (JSON, CSV, text formats)
- Restored output file support to trakt sync command
- Works alongside database storage or independently

The implementation addresses the feedback to maintain CLI functionality for starting scans and retrieving results while keeping scan and probe results database-driven, with JSON output as a supported secondary option.

(#174) '''
        branch = 'copilot/fix-174'
        
        issue_num, location = self.detect_issue_reference(title, body, branch)
        
        self.assertIsNotNone(issue_num, "Should detect issue reference in body")
        self.assertEqual(issue_num, '174', "Should extract correct issue number")
        self.assertEqual(location, 'body', "Should find issue in body")

    def test_title_reference(self):
        """Test issue reference in title"""
        title = 'feat: add new feature (#123)'
        body = 'This is a feature'
        branch = 'feature-branch'
        
        issue_num, location = self.detect_issue_reference(title, body, branch)
        
        self.assertEqual(issue_num, '123')
        self.assertEqual(location, 'title')

    def test_body_fixes_reference(self):
        """Test 'Fixes #123' pattern in body"""
        title = 'feat: add new feature'
        body = 'This fixes some issues.\n\nFixes #456'
        branch = 'feature-branch'
        
        issue_num, location = self.detect_issue_reference(title, body, branch)
        
        self.assertEqual(issue_num, '456')
        self.assertEqual(location, 'body')

    def test_body_closes_reference(self):
        """Test 'Closes #123' pattern in body"""
        title = 'fix: resolve bug'
        body = 'This change resolves the issue.\n\nCloses #789'
        branch = 'fix-branch'
        
        issue_num, location = self.detect_issue_reference(title, body, branch)
        
        self.assertEqual(issue_num, '789')
        self.assertEqual(location, 'body')

    def test_branch_issue_pattern(self):
        """Test issue-123-description branch pattern"""
        title = 'feat: add new feature'
        body = 'This is a feature'
        branch = 'issue-789-add-feature'
        
        issue_num, location = self.detect_issue_reference(title, body, branch)
        
        self.assertEqual(issue_num, '789')
        self.assertEqual(location, 'branch (pattern)')

    def test_branch_fix_pattern(self):
        """Test fix-123-description branch pattern"""
        title = 'fix: resolve issue'
        body = 'This fixes an issue'
        branch = 'fix-456-resolve-bug'
        
        issue_num, location = self.detect_issue_reference(title, body, branch)
        
        self.assertEqual(issue_num, '456')
        self.assertEqual(location, 'branch (pattern)')

    def test_branch_direct_reference(self):
        """Test direct #123 reference in branch name"""
        title = 'feat: add feature'
        body = 'This is a feature'
        branch = 'feature-#123'
        
        issue_num, location = self.detect_issue_reference(title, body, branch)
        
        self.assertEqual(issue_num, '123')
        self.assertEqual(location, 'branch (direct)')

    def test_no_reference(self):
        """Test case where no issue reference is found"""
        title = 'feat: add new feature'
        body = 'This is a feature with no issue reference'
        branch = 'feature-branch'
        
        issue_num, location = self.detect_issue_reference(title, body, branch)
        
        self.assertIsNone(issue_num)
        self.assertIsNone(location)

    def test_multiple_references_precedence(self):
        """Test that title takes precedence over body and branch"""
        title = 'feat: add new feature (#111)'
        body = 'This fixes issue #222'
        branch = 'issue-333-feature'
        
        issue_num, location = self.detect_issue_reference(title, body, branch)
        
        self.assertEqual(issue_num, '111')
        self.assertEqual(location, 'title')

    def test_body_over_branch_precedence(self):
        """Test that body takes precedence over branch"""
        title = 'feat: add new feature'
        body = 'This fixes issue #222'
        branch = 'issue-333-feature'
        
        issue_num, location = self.detect_issue_reference(title, body, branch)
        
        self.assertEqual(issue_num, '222')
        self.assertEqual(location, 'body')

    def test_empty_or_null_inputs(self):
        """Test handling of empty or null inputs"""
        # Test empty strings
        issue_num, location = self.detect_issue_reference('', '', '')
        self.assertIsNone(issue_num)
        
        # Test None body (like the original bug scenario)
        issue_num, location = self.detect_issue_reference('feat: test', None, 'test-branch')
        self.assertIsNone(issue_num)

    def test_various_issue_formats(self):
        """Test various formats of issue references"""
        test_cases = [
            ('Simple reference', 'Fix #123', '123'),
            ('Parentheses', 'Fix (#123)', '123'),
            ('At end', 'Fix issue (#123)', '123'),
            ('Multiple digits', 'Fix #12345', '12345'),
            ('With text after', 'Fix #123 and other things', '123'),
        ]
        
        for test_name, body_text, expected_num in test_cases:
            with self.subTest(test=test_name):
                issue_num, location = self.detect_issue_reference('title', body_text, 'branch')
                self.assertEqual(issue_num, expected_num)
                self.assertEqual(location, 'body')


if __name__ == '__main__':
    unittest.main()