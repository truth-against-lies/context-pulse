"""
Tests for ContextPulse.

Each function starting with test_ checks that part of the code works correctly.
When running pytest, it finds all these functions and runs them.
If something breaks — the test fails and you know what to fix.

To run: pytest tests/
"""

import sys
import os

# Add the root directory to path so we can import the code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contextpulse.config import get_category
from contextpulse.reports import (
    group_by_category,
    generate_summary,
    get_hot_files,
    group_by_directory,
)


# === Tests for get_category ===

def test_category_html():
    """Check that HTML files are identified correctly."""
    assert get_category("index.html") == "HTML"


def test_category_python():
    """Check that Python files are identified correctly."""
    assert get_category("main.py") == "Python"


def test_category_css():
    """Check that CSS files are identified as Style."""
    assert get_category("style.css") == "Style"


def test_category_javascript():
    """Check that JS files are identified correctly."""
    assert get_category("app.js") == "JavaScript"


def test_category_unknown():
    """Check that unknown files get "Other"."""
    assert get_category("data.xyz") == "Other"


def test_category_image():
    """Check that images are identified."""
    assert get_category("photo.png") == "Images"
    assert get_category("logo.svg") == "Images"


def test_category_config():
    """Check that config files are identified."""
    assert get_category("package.json") == "Config"
    assert get_category("config.yml") == "Config"


def test_category_case_insensitive():
    """Check that identification is case-insensitive."""
    assert get_category("INDEX.HTML") == "HTML"
    assert get_category("Style.CSS") == "Style"


# === Tests for group_by_category ===

def make_fake_commits(files_list):
    """Creates fake commits for testing."""
    commits = []
    for files in files_list:
        commits.append({
            "hash": "abc1234",
            "message": "test commit",
            "author": "tester",
            "date": "2026-01-01 12:00",
            "date_short": "2026-01-01",
            "files_changed": len(files),
            "files": files,
        })
    return commits


def test_group_by_category():
    """Check that grouping by category works."""
    commits = make_fake_commits([
        ["index.html", "style.css"],
        ["index.html", "app.js"],
    ])
    categories = group_by_category(commits)

    assert categories["HTML"]["commits"] == 2
    assert categories["Style"]["commits"] == 1
    assert categories["JavaScript"]["commits"] == 1


# === Tests for get_hot_files ===

def test_hot_files():
    """Check that most active files are identified."""
    commits = make_fake_commits([
        ["a.py", "b.py"],
        ["a.py", "c.py"],
        ["a.py"],
    ])
    hot = get_hot_files(commits, top_n=2)

    assert hot[0][0] == "a.py"
    assert hot[0][1] == 3
    assert len(hot) == 2


# === Tests for generate_summary ===

def test_summary_with_fixes():
    """Check that summary detects bug fixes."""
    commits = make_fake_commits([["a.html"]])
    commits[0]["message"] = "Fix broken button"
    categories = group_by_category(commits)
    summary = generate_summary(commits, categories)

    assert "bug fixes" in summary
    assert "1 commits" in summary


def test_summary_empty():
    """Check that empty summary returns appropriate message."""
    summary = generate_summary([], {})
    assert "No activity" in summary


# === Tests for group_by_directory ===

def test_group_by_directory():
    """Check that grouping by directory works."""
    commits = make_fake_commits([
        ["src/app.py", "src/utils.py", "README.md"],
    ])
    dirs = group_by_directory(commits)

    assert "src" in dirs
    assert dirs["src"]["commits"] == 2
    assert "(root)" in dirs
