#!/usr/bin/env python3
"""
Unit tests for parse_branch.py
"""

import unittest
from parse_branch import parse_branch_name, parse_all_branch_names, extract_text_and_branch


class TestParseBranch(unittest.TestCase):
    """Test cases for branch name parsing functions."""

    def test_parse_simple_branch(self):
        """Test parsing a simple branch name."""
        result = parse_branch_name("@@feature/new-api")
        self.assertEqual(result, "feature/new-api")

    def test_parse_branch_in_sentence(self):
        """Test parsing branch name within a sentence."""
        result = parse_branch_name("Please create @@bugfix/login-error for this issue")
        self.assertEqual(result, "bugfix/login-error")

    def test_parse_branch_with_numbers(self):
        """Test parsing branch name with numbers."""
        result = parse_branch_name("@@release/v1.2.3")
        self.assertEqual(result, "release/v1.2.3")

    def test_parse_branch_with_underscores(self):
        """Test parsing branch name with underscores."""
        result = parse_branch_name("@@feature/user_authentication")
        self.assertEqual(result, "feature/user_authentication")

    def test_no_branch_found(self):
        """Test when no branch pattern is found."""
        result = parse_branch_name("No branch here")
        self.assertIsNone(result)

    def test_parse_multiple_branches_returns_first(self):
        """Test that parse_branch_name returns only the first match."""
        result = parse_branch_name("@@feature/a and @@feature/b")
        self.assertEqual(result, "feature/a")

    def test_parse_all_branches(self):
        """Test parsing all branch names."""
        result = parse_all_branch_names("@@feature/a and @@feature/b")
        self.assertEqual(result, ["feature/a", "feature/b"])

    def test_parse_all_branches_empty(self):
        """Test parsing when no branches exist."""
        result = parse_all_branch_names("No branches here")
        self.assertEqual(result, [])

    def test_extract_text_and_branch(self):
        """Test extracting both text and branch name."""
        text, branch = extract_text_and_branch("Create @@feature/api endpoint")
        self.assertEqual(text, "Create  endpoint")
        self.assertEqual(branch, "feature/api")

    def test_extract_text_and_branch_no_branch(self):
        """Test extracting when no branch exists."""
        text, branch = extract_text_and_branch("Just some text")
        self.assertEqual(text, "Just some text")
        self.assertIsNone(branch)

    def test_japanese_text_with_branch(self):
        """Test parsing branch from Japanese text."""
        result = parse_branch_name("@@feature/new-apiを作成してください")
        self.assertEqual(result, "feature/new-api")


if __name__ == '__main__':
    unittest.main()
