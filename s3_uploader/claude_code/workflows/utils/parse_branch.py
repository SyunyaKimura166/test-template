#!/usr/bin/env python3
"""
Branch name parser utility.

This script parses branch names from text using the @@<branch_name> format.
"""

import re
from typing import Optional, List


def parse_branch_name(text: str) -> Optional[str]:
    """
    Parse a single branch name from text using the @@<branch_name> format.

    Args:
        text: Input text containing the branch name pattern

    Returns:
        The parsed branch name without the @@ prefix, or None if not found

    Examples:
        >>> parse_branch_name("@@feature/new-api")
        'feature/new-api'
        >>> parse_branch_name("Please create @@bugfix/login-error")
        'bugfix/login-error'
        >>> parse_branch_name("No branch here")
        None
    """
    # Pattern: @@ followed by branch name (alphanumeric, -, _, /, .)
    pattern = r'@@([a-zA-Z0-9/_.-]+)'
    match = re.search(pattern, text)

    if match:
        return match.group(1)
    return None


def parse_all_branch_names(text: str) -> List[str]:
    """
    Parse all branch names from text using the @@<branch_name> format.

    Args:
        text: Input text containing one or more branch name patterns

    Returns:
        List of all parsed branch names without the @@ prefix

    Examples:
        >>> parse_all_branch_names("@@feature/a and @@feature/b")
        ['feature/a', 'feature/b']
        >>> parse_all_branch_names("No branches")
        []
    """
    # Pattern: @@ followed by branch name (alphanumeric, -, _, /, .)
    pattern = r'@@([a-zA-Z0-9/_.-]+)'
    matches = re.findall(pattern, text)

    return matches


def extract_text_and_branch(text: str) -> tuple[str, Optional[str]]:
    """
    Extract both the branch name and the text without the branch marker.

    Args:
        text: Input text containing the branch name pattern

    Returns:
        Tuple of (cleaned_text, branch_name)

    Examples:
        >>> extract_text_and_branch("Create @@feature/api endpoint")
        ('Create  endpoint', 'feature/api')
    """
    branch_name = parse_branch_name(text)

    if branch_name:
        # Remove the @@branch_name from text
        cleaned_text = re.sub(r'@@[a-zA-Z0-9/_.-]+', '', text).strip()
        return cleaned_text, branch_name

    return text, None


if __name__ == '__main__':
    import sys

    # If called directly, parse branch name from command line arguments or stdin
    if len(sys.argv) > 1:
        # Parse from command line argument
        input_text = ' '.join(sys.argv[1:])
    else:
        # Read from stdin
        input_text = sys.stdin.read().strip()

    if not input_text:
        print("Usage: parse_branch.py <text_with_branch>", file=sys.stderr)
        print("   or: echo 'text with @@branch' | parse_branch.py", file=sys.stderr)
        sys.exit(1)

    branch = parse_branch_name(input_text)

    if branch:
        print(branch)
        sys.exit(0)
    else:
        print("No branch name found in the input text", file=sys.stderr)
        sys.exit(1)
