"""
בדיקות ל-ContextPulse.

מה זה בדיקות (tests)?
כל פונקציה שמתחילה ב-test_ בודקת שחלק מהקוד עובד נכון.
כשמריצים pytest, הוא מחפש את כל הפונקציות האלה ומריץ אותן.
אם משהו נשבר — הבדיקה נכשלת ואתה יודע מה לתקן.

להריץ: pytest tests/
"""

import sys
import os

# מוסיפים את התיקייה הראשית ל-path כדי שנוכל לייבא את הקוד
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contextpulse.main import (
    get_category,
    group_by_category,
    generate_summary,
    get_hot_files,
    group_by_directory,
)


# === בדיקות לפונקציית get_category ===

def test_category_html():
    """בודק שקובץ HTML מזוהה נכון."""
    assert get_category("index.html") == "HTML"


def test_category_python():
    """בודק שקובץ Python מזוהה נכון."""
    assert get_category("main.py") == "Python"


def test_category_css():
    """בודק שקובץ CSS מזוהה כ-Style."""
    assert get_category("style.css") == "Style"


def test_category_javascript():
    """בודק שקובץ JS מזוהה נכון."""
    assert get_category("app.js") == "JavaScript"


def test_category_unknown():
    """בודק שקובץ לא מוכר מקבל "Other"."""
    assert get_category("data.xyz") == "Other"


def test_category_image():
    """בודק שתמונות מזוהות."""
    assert get_category("photo.png") == "Images"
    assert get_category("logo.svg") == "Images"


def test_category_config():
    """בודק שקבצי הגדרות מזוהים."""
    assert get_category("package.json") == "Config"
    assert get_category("config.yml") == "Config"


def test_category_case_insensitive():
    """בודק שהזיהוי לא תלוי באותיות גדולות/קטנות."""
    assert get_category("INDEX.HTML") == "HTML"
    assert get_category("Style.CSS") == "Style"


# === בדיקות לפונקציית group_by_category ===

def make_fake_commits(files_list):
    """יוצר קומיטים מזויפים לבדיקות."""
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
    """בודק שהקיבוץ לפי קטגוריה עובד."""
    commits = make_fake_commits([
        ["index.html", "style.css"],
        ["index.html", "app.js"],
    ])
    categories = group_by_category(commits)

    assert categories["HTML"]["commits"] == 2  # index.html הופיע פעמיים
    assert categories["Style"]["commits"] == 1
    assert categories["JavaScript"]["commits"] == 1


# === בדיקות לפונקציית get_hot_files ===

def test_hot_files():
    """בודק שהקבצים הכי פעילים מזוהים."""
    commits = make_fake_commits([
        ["a.py", "b.py"],
        ["a.py", "c.py"],
        ["a.py"],
    ])
    hot = get_hot_files(commits, top_n=2)

    assert hot[0][0] == "a.py"   # a.py הופיע 3 פעמים — הכי חם
    assert hot[0][1] == 3
    assert len(hot) == 2          # ביקשנו רק top 2


# === בדיקות לפונקציית generate_summary ===

def test_summary_with_fixes():
    """בודק שהסיכום מזהה bug fixes."""
    commits = make_fake_commits([["a.html"]])
    commits[0]["message"] = "Fix broken button"
    categories = group_by_category(commits)
    summary = generate_summary(commits, categories)

    assert "bug fixes" in summary
    assert "1 commits" in summary


def test_summary_empty():
    """בודק שסיכום ריק מחזיר הודעה מתאימה."""
    summary = generate_summary([], {})
    assert "No activity" in summary


# === בדיקות לפונקציית group_by_directory ===

def test_group_by_directory():
    """בודק שהקיבוץ לפי תיקיות עובד."""
    commits = make_fake_commits([
        ["src/app.py", "src/utils.py", "README.md"],
    ])
    dirs = group_by_directory(commits)

    assert "src" in dirs
    assert dirs["src"]["commits"] == 2
    assert "(root)" in dirs  # README.md נמצא בשורש
