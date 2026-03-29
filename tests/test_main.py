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

from contextpulse.config import (
    get_category,
    _cat_to_hex,
    t,
    th,
    CATEGORY_MAP,
    CATEGORY_COLORS,
    TRANSLATIONS,
    THEMES,
)
from contextpulse.reports import (
    group_by_category,
    generate_summary,
    get_hot_files,
    group_by_directory,
)
from contextpulse.smart import expand_shortcuts, SHORTCUTS


# ================================================================
# Helper: creates fake commits for testing
# ================================================================

def make_fake_commits(files_list, messages=None):
    """Creates fake commits for testing."""
    commits = []
    for i, files in enumerate(files_list):
        msg = messages[i] if messages and i < len(messages) else "test commit"
        commits.append({
            "hash": f"abc{i:04d}",
            "message": msg,
            "author": "tester",
            "date": "2026-01-01 12:00",
            "date_short": "2026-01-01",
            "hour": 14,
            "weekday": "Monday",
            "files_changed": len(files),
            "files": files,
            "insertions": 10,
            "deletions": 2,
        })
    return commits


# ================================================================
# config.py tests — get_category
# ================================================================

def test_category_html():
    assert get_category("index.html") == "HTML"


def test_category_python():
    assert get_category("main.py") == "Python"


def test_category_css():
    assert get_category("style.css") == "Style"


def test_category_javascript():
    assert get_category("app.js") == "JavaScript"


def test_category_typescript():
    assert get_category("app.ts") == "TypeScript"
    assert get_category("component.tsx") == "TypeScript"


def test_category_unknown():
    assert get_category("data.xyz") == "Other"


def test_category_image():
    assert get_category("photo.png") == "Images"
    assert get_category("logo.svg") == "Images"
    assert get_category("icon.webp") == "Images"


def test_category_config():
    assert get_category("package.json") == "Config"
    assert get_category("config.yml") == "Config"
    assert get_category("settings.toml") == "Config"


def test_category_docs():
    assert get_category("README.md") == "Docs"
    assert get_category("notes.txt") == "Docs"


def test_category_shell():
    assert get_category("deploy.sh") == "Shell"
    assert get_category("setup.bash") == "Shell"


def test_category_database():
    assert get_category("schema.sql") == "Database"


def test_category_case_insensitive():
    assert get_category("INDEX.HTML") == "HTML"
    assert get_category("Style.CSS") == "Style"
    assert get_category("APP.PY") == "Python"


def test_category_with_path():
    assert get_category("src/components/Button.tsx") == "TypeScript"
    assert get_category("public/style.css") == "Style"


# ================================================================
# config.py tests — _cat_to_hex
# ================================================================

def test_cat_to_hex_known():
    assert _cat_to_hex("Python") == "#3fb950"
    assert _cat_to_hex("HTML") == "#f85149"


def test_cat_to_hex_unknown():
    assert _cat_to_hex("Unknown") == "#8b949e"


# ================================================================
# config.py tests — translations
# ================================================================

def test_translation_english():
    assert t("summary") == "Summary"
    assert t("commits") == "Commits"


def test_translation_missing_key():
    result = t("nonexistent_key_12345")
    assert result == "nonexistent_key_12345"


def test_translations_have_same_keys():
    en_keys = set(TRANSLATIONS["en"].keys())
    he_keys = set(TRANSLATIONS["he"].keys())
    assert en_keys == he_keys, f"Missing in HE: {en_keys - he_keys}"


# ================================================================
# config.py tests — themes
# ================================================================

def test_theme_default_exists():
    assert "default" in THEMES
    assert "title" in THEMES["default"]


def test_theme_all_have_required_keys():
    required = {"title", "subtitle", "header", "border", "accent", "positive", "negative"}
    for name, theme in THEMES.items():
        for key in required:
            assert key in theme, f"Theme '{name}' missing '{key}'"


def test_th_returns_string():
    result = th("title")
    assert isinstance(result, str)


# ================================================================
# reports.py tests — group_by_category
# ================================================================

def test_group_by_category():
    commits = make_fake_commits([
        ["index.html", "style.css"],
        ["index.html", "app.js"],
    ])
    categories = group_by_category(commits)
    assert categories["HTML"]["commits"] == 2
    assert categories["Style"]["commits"] == 1
    assert categories["JavaScript"]["commits"] == 1


def test_group_by_category_empty():
    categories = group_by_category([])
    assert len(categories) == 0


# ================================================================
# reports.py tests — get_hot_files
# ================================================================

def test_hot_files():
    commits = make_fake_commits([
        ["a.py", "b.py"],
        ["a.py", "c.py"],
        ["a.py"],
    ])
    hot = get_hot_files(commits, top_n=2)
    assert hot[0][0] == "a.py"
    assert hot[0][1] == 3
    assert len(hot) == 2


def test_hot_files_empty():
    hot = get_hot_files([], top_n=5)
    assert hot == []


def test_hot_files_top_1():
    commits = make_fake_commits([["x.py", "y.py"], ["x.py"]])
    hot = get_hot_files(commits, top_n=1)
    assert len(hot) == 1
    assert hot[0][0] == "x.py"


# ================================================================
# reports.py tests — generate_summary
# ================================================================

def test_summary_with_fixes():
    commits = make_fake_commits([["a.html"]], messages=["Fix broken button"])
    categories = group_by_category(commits)
    summary = generate_summary(commits, categories)
    assert "bug fixes" in summary
    assert "1 commit" in summary


def test_summary_with_add():
    commits = make_fake_commits([["a.py"]], messages=["Add new feature"])
    categories = group_by_category(commits)
    summary = generate_summary(commits, categories)
    assert "new features" in summary


def test_summary_with_refactor():
    commits = make_fake_commits([["a.py"]], messages=["Refactor auth module"])
    categories = group_by_category(commits)
    summary = generate_summary(commits, categories)
    assert "refactoring" in summary


def test_summary_empty():
    summary = generate_summary([], {})
    assert "No activity" in summary


def test_summary_multiple_categories():
    commits = make_fake_commits([
        ["a.html", "b.css", "c.js"],
    ])
    categories = group_by_category(commits)
    summary = generate_summary(commits, categories)
    assert "Also touched" in summary


# ================================================================
# reports.py tests — group_by_directory
# ================================================================

def test_group_by_directory():
    commits = make_fake_commits([
        ["src/app.py", "src/utils.py", "README.md"],
    ])
    dirs = group_by_directory(commits)
    assert "src" in dirs
    assert dirs["src"]["commits"] == 2
    assert "(root)" in dirs


def test_group_by_directory_all_root():
    commits = make_fake_commits([["a.py", "b.js"]])
    dirs = group_by_directory(commits)
    assert "(root)" in dirs
    assert len(dirs) == 1


def test_group_by_directory_nested():
    commits = make_fake_commits([
        ["src/components/Button.tsx", "src/utils/helpers.py"],
    ])
    dirs = group_by_directory(commits)
    assert "src" in dirs
    assert dirs["src"]["commits"] == 2


# ================================================================
# smart.py tests — expand_shortcuts
# ================================================================

def test_shortcut_today():
    result = expand_shortcuts(["today"])
    assert result == ["--today"]


def test_shortcut_month():
    result = expand_shortcuts(["month"])
    assert result == ["--month"]


def test_shortcut_week():
    result = expand_shortcuts(["week"])
    assert result == ["--week"]


def test_shortcut_json():
    result = expand_shortcuts(["json"])
    assert result == ["--json"]


def test_shortcut_empty():
    result = expand_shortcuts([])
    assert result == []


def test_shortcut_unknown_passes_through():
    result = expand_shortcuts(["--days", "5"])
    assert result == ["--days", "5"]


def test_shortcut_since_with_date():
    result = expand_shortcuts(["since", "2026-03-01"])
    assert result == ["--since", "2026-03-01"]


def test_shortcut_scan_returns_none():
    # scan runs the function directly and returns None
    result = expand_shortcuts(["scan", "/nonexistent/path"])
    assert result is None


def test_shortcuts_dict_has_expected_keys():
    expected = {"today", "week", "month", "json", "scan", "team",
                "hours", "vs", "streak", "log", "help", "diff", "blame"}
    for key in expected:
        assert key in SHORTCUTS, f"Missing shortcut: {key}"


# ================================================================
# smart.py tests — Hebrew shortcuts
# ================================================================

def test_hebrew_today():
    result = expand_shortcuts(["היום"])
    assert result == ["--today"]


def test_hebrew_week():
    result = expand_shortcuts(["שבוע"])
    assert result == ["--week"]


def test_hebrew_month():
    result = expand_shortcuts(["חודש"])
    assert result == ["--month"]


def test_hebrew_help_returns_none():
    # help runs the function directly
    result = expand_shortcuts(["עזרה"])
    assert result is None
