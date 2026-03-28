"""
ContextPulse - Turn your Git history into a human story.

Usage (full flags):
    pulse                        # last 7 days (default)
    pulse --today                # today only
    pulse --days 3               # last 3 days
    pulse --month                # last 30 days
    pulse --since 2026-03-01     # from a specific date
    pulse --author "John"        # filter by author name
    pulse --export report.md     # save as Markdown file
    pulse --json                 # output as JSON
    pulse --compare main..dev    # compare two branches
    pulse --interactive          # choose from a menu
    pulse ~/code/my-project      # scan a specific repo

Lazy shortcuts (same thing, less typing):
    pulse today                  # = pulse --today
    pulse week                   # = pulse --week
    pulse month                  # = pulse --month
    pulse since 2026-03-01       # = pulse --since 2026-03-01
    pulse json                   # = pulse --json
    pulse i                      # = pulse --interactive
    pulse scan                   # code quality + structure report
    pulse scan ~/code/project    # scan a specific repo
"""

# === ייבוא ספריות ===
# argparse = מאפשר לקבל פרמטרים מהטרמינל (כמו --days 30)
# collections = כלים לעבודה עם רשימות ומילונים (defaultdict, Counter)
# datetime = עבודה עם תאריכים
# json = המרה לפורמט JSON (מבנה נתונים אוניברסלי)
# pathlib = עבודה עם נתיבי קבצים
# sys = גישה לפרמטרים של המערכת (כמו exit)
# os = בדיקת קיום תיקיות ונתיבים
# git = קריאת היסטוריית Git דרך Python
# rich = הדפסה יפה בטרמינל (צבעים, טבלאות, גרפים)
import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table

console = Console()

# === מיפוי קבצים לקטגוריות ===
CATEGORY_MAP = {
    ".html": "HTML", ".css": "Style", ".js": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".jsx": "JavaScript",
    ".py": "Python", ".rb": "Ruby", ".go": "Go", ".rs": "Rust",
    ".java": "Java", ".kt": "Kotlin", ".swift": "Swift",
    ".c": "C/C++", ".cpp": "C/C++", ".h": "C/C++",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".json": "Config", ".yml": "Config", ".yaml": "Config",
    ".toml": "Config", ".ini": "Config", ".env": "Config",
    ".xml": "Config", ".lock": "Config",
    ".md": "Docs", ".txt": "Docs", ".rst": "Docs",
    ".png": "Images", ".jpg": "Images", ".jpeg": "Images",
    ".svg": "Images", ".gif": "Images", ".webp": "Images", ".ico": "Images",
    ".sql": "Database", ".csv": "Data", ".parquet": "Data",
    ".test.js": "Tests", ".spec.js": "Tests", ".test.py": "Tests",
}

# === צבע לכל קטגוריה ===
CATEGORY_COLORS = {
    "HTML": "bright_red",
    "Style": "bright_blue",
    "JavaScript": "bright_yellow",
    "TypeScript": "yellow",
    "Python": "bright_green",
    "Ruby": "red",
    "Go": "cyan",
    "Rust": "bright_red",
    "Java": "red",
    "Kotlin": "magenta",
    "Swift": "bright_red",
    "C/C++": "blue",
    "Shell": "green",
    "Config": "bright_magenta",
    "Docs": "bright_white",
    "Images": "bright_cyan",
    "Database": "blue",
    "Data": "magenta",
    "Tests": "green",
    "Other": "dim",
}

# === תרגומים ===
# כל טקסט שמופיע למשתמש עובר דרך המילון הזה.
# ברירת מחדל = אנגלית. עם --lang he = עברית.
TRANSLATIONS = {
    "en": {
        "starting": "starting...",
        "summary": "Summary",
        "commits": "Commits",
        "changes_by_cat": "Changes by Category",
        "hot_files": "Hot Files (most changed)",
        "changes_by_dir": "Changes by Directory",
        "daily_activity": "Daily Activity",
        "total": "Total",
        "commits_word": "commits",
        "by": "by",
        "author_s": "author(s)",
        "file_changes": "file changes",
        "lines_added": "lines added",
        "lines_removed": "lines removed",
        "net": "net",
        "no_commits": "No commits found in this period.",
        "report_title": "Git Activity Report",
        "team_report": "Team Report",
        "contributors": "Contributors",
        "work_patterns": "Work Patterns",
        "activity_by_hour": "Activity by Hour",
        "activity_by_day": "Activity by Day",
        "peak_hour": "Peak hour",
        "peak_day": "Peak day",
        "pattern": "Pattern",
        "period_comparison": "Period Comparison",
        "current": "Current",
        "previous": "Previous",
        "change": "Change",
        "productivity_up": "Productivity up!",
        "slower_period": "Slower period.",
        "same_pace": "Same pace as before.",
        "project_health": "Project Health",
        "quality_check": "Quality Check",
        "project_structure": "Project Structure",
        "file_types": "File Types in Project",
        "largest_files": "Largest Files",
        "report_saved": "Report saved to",
        "you_made": "You made",
        "focusing_on": "focusing mainly on",
        "main_activities": "Main activities",
        "also_touched": "Also touched",
        "bug_fixes": "bug fixes",
        "new_features": "new features",
        "improvements": "improvements",
        "refactoring": "refactoring",
        "testing": "testing",
        "documentation": "documentation",
        "various": "various changes",
        "morning_person": "morning person (6-12)",
        "afternoon_coder": "afternoon coder (12-18)",
        "evening_hacker": "evening hacker (18-22)",
        "night_owl": "night owl (22-06)",
        "youre_a": "You're a",
    },
    "he": {
        "starting": "מתחיל...",
        "summary": "סיכום",
        "commits": "קומיטים",
        "changes_by_cat": "שינויים לפי קטגוריה",
        "hot_files": "קבצים חמים (הכי השתנו)",
        "changes_by_dir": "שינויים לפי תיקייה",
        "daily_activity": "פעילות יומית",
        "total": "סה״כ",
        "commits_word": "קומיטים",
        "by": "ע״י",
        "author_s": "מחבר/ים",
        "file_changes": "שינויי קבצים",
        "lines_added": "שורות נוספו",
        "lines_removed": "שורות נמחקו",
        "net": "נטו",
        "no_commits": "לא נמצאו קומיטים בתקופה הזו.",
        "report_title": "דוח פעילות Git",
        "team_report": "דוח צוות",
        "contributors": "תורמים",
        "work_patterns": "דפוסי עבודה",
        "activity_by_hour": "פעילות לפי שעה",
        "activity_by_day": "פעילות לפי יום",
        "peak_hour": "שעת שיא",
        "peak_day": "יום שיא",
        "pattern": "דפוס",
        "period_comparison": "השוואת תקופות",
        "current": "נוכחי",
        "previous": "קודם",
        "change": "שינוי",
        "productivity_up": "פרודוקטיביות עלתה!",
        "slower_period": "תקופה איטית יותר.",
        "same_pace": "אותו קצב כמו קודם.",
        "project_health": "בריאות הפרויקט",
        "quality_check": "בדיקת איכות",
        "project_structure": "מבנה הפרויקט",
        "file_types": "סוגי קבצים בפרויקט",
        "largest_files": "הקבצים הגדולים ביותר",
        "report_saved": "הדוח נשמר ב",
        "you_made": "ביצעת",
        "focusing_on": "בדגש על",
        "main_activities": "פעילויות עיקריות",
        "also_touched": "גם נגעת ב",
        "bug_fixes": "תיקוני באגים",
        "new_features": "פיצ׳רים חדשים",
        "improvements": "שיפורים",
        "refactoring": "ריפקטורינג",
        "testing": "בדיקות",
        "documentation": "תיעוד",
        "various": "שינויים שונים",
        "morning_person": "אדם של בוקר (6-12)",
        "afternoon_coder": "מתכנת צהריים (12-18)",
        "evening_hacker": "האקר ערב (18-22)",
        "night_owl": "ינשוף לילה (22-06)",
        "youre_a": "אתה",
    },
}

# שפה פעילה — ברירת מחדל אנגלית
current_lang = "en"


def t(key):
    """מחזיר טקסט מתורגם לפי השפה הפעילה."""
    return TRANSLATIONS.get(current_lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )


# === ערכות נושא (Themes) ===
# כל theme מגדיר צבעים לחלקים שונים בדוח
THEMES = {
    "default": {
        "title": "bold cyan",
        "subtitle": "dim",
        "header": "bold magenta",
        "border": "cyan",
        "summary_border": "green",
        "accent": "cyan",
        "positive": "green",
        "negative": "red",
        "neutral": "dim",
    },
    "ocean": {
        "title": "bold blue",
        "subtitle": "dim cyan",
        "header": "bold cyan",
        "border": "blue",
        "summary_border": "cyan",
        "accent": "bright_blue",
        "positive": "bright_cyan",
        "negative": "bright_red",
        "neutral": "dim",
    },
    "forest": {
        "title": "bold green",
        "subtitle": "dim",
        "header": "bold bright_green",
        "border": "green",
        "summary_border": "bright_green",
        "accent": "green",
        "positive": "bright_green",
        "negative": "red",
        "neutral": "dim",
    },
    "sunset": {
        "title": "bold bright_red",
        "subtitle": "dim yellow",
        "header": "bold yellow",
        "border": "bright_red",
        "summary_border": "yellow",
        "accent": "bright_yellow",
        "positive": "yellow",
        "negative": "red",
        "neutral": "dim",
    },
    "minimal": {
        "title": "bold white",
        "subtitle": "dim",
        "header": "bold white",
        "border": "white",
        "summary_border": "white",
        "accent": "white",
        "positive": "green",
        "negative": "red",
        "neutral": "dim",
    },
}

current_theme = THEMES["default"]


def th(key):
    """מחזיר צבע לפי ה-theme הפעיל."""
    return current_theme.get(key, "white")


def get_category(filename):
    """
    מקבל שם קובץ ומחזיר את הקטגוריה שלו.
    בודק קודם סיומות כפולות (כמו .test.js) ואז סיומות רגילות.
    """
    name_lower = filename.lower()
    # בדיקת סיומות כפולות (לזיהוי קבצי טסטים)
    for ext, cat in CATEGORY_MAP.items():
        if "." in ext[1:] and name_lower.endswith(ext):
            return cat
    suffix = Path(filename).suffix.lower()
    return CATEGORY_MAP.get(suffix, "Other")


def get_commits(repo_path=".", days=7, author_filter=None):
    """
    קורא קומיטים מהריפוזיטורי.
    repo_path = נתיב לריפו ("." = תיקייה נוכחית)
    days = כמה ימים אחורה (ברירת מחדל: 7)
    author_filter = סינון לפי שם מחבר (אופציונלי)
    """
    repo = Repo(repo_path)
    since_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

    commits = []
    for commit in repo.iter_commits():
        if commit.committed_date < since_date:
            break

        if author_filter:
            author_name = str(commit.author).lower()
            if author_filter.lower() not in author_name:
                continue

        changed_files = list(commit.stats.files.keys())

        # שורות שנוספו/נמחקו — commit.stats.total נותן סה"כ
        insertions = commit.stats.total.get("insertions", 0)
        deletions = commit.stats.total.get("deletions", 0)

        commit_dt = datetime.fromtimestamp(commit.committed_date)
        commits.append({
            "hash": commit.hexsha[:7],
            "message": commit.message.strip().split("\n")[0],
            "author": str(commit.author),
            "date": commit_dt.strftime("%Y-%m-%d %H:%M"),
            "date_short": commit_dt.strftime("%Y-%m-%d"),
            "hour": commit_dt.hour,
            "weekday": commit_dt.strftime("%A"),
            "files_changed": len(changed_files),
            "files": changed_files,
            "insertions": insertions,
            "deletions": deletions,
        })

    return commits


def get_compare_commits(repo_path, compare_str):
    """
    משווה בין שני branches ומחזיר את הקומיטים שביניהם.
    compare_str = "main..dev" — מה שונה ב-dev לעומת main
    """
    repo = Repo(repo_path)

    if ".." not in compare_str:
        console.print(
            "[red]Error:[/red] Use format: branch1..branch2 "
            "(e.g., main..dev)"
        )
        return []

    base, target = compare_str.split("..", 1)

    try:
        compare_commits = list(repo.iter_commits(f"{base}..{target}"))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return []

    commits = []
    for commit in compare_commits:
        changed_files = list(commit.stats.files.keys())
        commit_dt = datetime.fromtimestamp(commit.committed_date)
        commits.append({
            "hash": commit.hexsha[:7],
            "message": commit.message.strip().split("\n")[0],
            "author": str(commit.author),
            "date": commit_dt.strftime("%Y-%m-%d %H:%M"),
            "date_short": commit_dt.strftime("%Y-%m-%d"),
            "hour": commit_dt.hour,
            "weekday": commit_dt.strftime("%A"),
            "files_changed": len(changed_files),
            "files": changed_files,
        })

    return commits


def group_by_category(commits):
    """מקבץ את כל השינויים לפי קטגוריה."""
    categories = defaultdict(lambda: {"commits": 0, "files": set()})

    for commit in commits:
        for filename in commit["files"]:
            cat = get_category(filename)
            categories[cat]["commits"] += 1
            categories[cat]["files"].add(filename)

    return categories


def group_by_directory(commits):
    """
    מקבץ שינויים לפי תיקיות (שימושי ל-monorepo).
    מסתכל על התיקייה הראשית של כל קובץ.
    למשל: "src/components/Button.tsx" → "src/components"
    """
    dirs = defaultdict(lambda: {"commits": 0, "files": set()})

    for commit in commits:
        for filename in commit["files"]:
            # לוקחים את התיקייה הראשית (או "root" אם הקובץ בשורש)
            parts = Path(filename).parts
            if len(parts) > 1:
                top_dir = parts[0]
            else:
                top_dir = "(root)"
            dirs[top_dir]["commits"] += 1
            dirs[top_dir]["files"].add(filename)

    return dirs


def get_hot_files(commits, top_n=5):
    """
    מוצא את הקבצים שהשתנו הכי הרבה פעמים ("נקודות חמות").
    קבצים שמשתנים הרבה = קבצים שכדאי לשים לב אליהם.
    """
    file_counts = Counter()
    for commit in commits:
        for filename in commit["files"]:
            file_counts[filename] += 1

    return file_counts.most_common(top_n)


def generate_summary(commits, categories):
    """יוצר סיכום טקסטואלי אנושי."""
    if not commits:
        return "No activity in this period."

    total_commits = len(commits)

    sorted_cats = sorted(
        categories.items(),
        key=lambda x: x[1]["commits"],
        reverse=True,
    )
    top_cat = sorted_cats[0][0] if sorted_cats else "code"

    total_cat_commits = sum(c["commits"] for c in categories.values())
    if total_cat_commits > 0:
        top_pct = round(
            sorted_cats[0][1]["commits"] / total_cat_commits * 100
        )
    else:
        top_pct = 0

    messages = " ".join(c["message"].lower() for c in commits)
    activities = []
    if "fix" in messages:
        activities.append("bug fixes")
    if "add" in messages:
        activities.append("new features")
    if "update" in messages or "improve" in messages:
        activities.append("improvements")
    if "refactor" in messages:
        activities.append("refactoring")
    if "test" in messages:
        activities.append("testing")
    if "doc" in messages or "readme" in messages:
        activities.append("documentation")
    if not activities:
        activities.append("various changes")

    activity_str = ", ".join(activities)
    summary = (
        f"You made {total_commits} commits, focusing mainly on "
        f"{top_cat} ({top_pct}%). "
        f"Main activities: {activity_str}."
    )

    if len(sorted_cats) > 1:
        others = [c[0] for c in sorted_cats[1:3]]
        summary += f" Also touched: {', '.join(others)}."

    return summary


def display_activity_chart(commits):
    """גרף פעילות — מראה באיזה ימים היית הכי פעיל."""
    if not commits:
        return

    day_counts = Counter(c["date_short"] for c in commits)
    sorted_days = sorted(day_counts.items())

    console.print()
    console.print("[bold]Daily Activity[/bold]")

    max_count = max(day_counts.values())

    for day, count in sorted_days:
        bar_len = round(count / max_count * 30)
        bar = "█" * bar_len

        if count <= max_count * 0.33:
            color = "green"
        elif count <= max_count * 0.66:
            color = "yellow"
        else:
            color = "red"

        console.print(f"  {day}  [{color}]{bar}[/{color}] {count}")


def display_hot_files(commits):
    """מציג את 5 הקבצים שהשתנו הכי הרבה."""
    hot = get_hot_files(commits)
    if not hot:
        return

    console.print()
    hot_table = Table(
        title="Hot Files (most changed)",
        show_header=True,
        header_style="bold red",
    )
    hot_table.add_column("#", style="dim", width=3)
    hot_table.add_column("File", style="white")
    hot_table.add_column("Changes", justify="right", style="red")

    for i, (filename, count) in enumerate(hot, 1):
        # מציגים אייקון "אש" לקבצים שהשתנו המון
        fire = "🔥 " if count >= 5 else "   "
        hot_table.add_row(str(i), f"{fire}{filename}", str(count))

    console.print(hot_table)


def display_directory_breakdown(commits):
    """מציג פירוט לפי תיקיות (שימושי ל-monorepo)."""
    dirs = group_by_directory(commits)
    if len(dirs) <= 1:
        return  # אם הכל בתיקייה אחת, לא רלוונטי

    console.print()
    dir_table = Table(
        title="Changes by Directory",
        show_header=True,
        header_style="bold yellow",
    )
    dir_table.add_column("Directory", style="bold")
    dir_table.add_column("Commits", justify="right", style="cyan")
    dir_table.add_column("Files", justify="right", style="green")

    sorted_dirs = sorted(
        dirs.items(),
        key=lambda x: x[1]["commits"],
        reverse=True,
    )
    for dir_name, data in sorted_dirs[:10]:  # מקסימום 10 תיקיות
        dir_table.add_row(
            dir_name,
            str(data["commits"]),
            str(len(data["files"])),
        )

    console.print(dir_table)


def display_report(commits, period_label):
    """מציג את הדוח המלא בטרמינל."""
    if not commits:
        console.print(
            Panel(t("no_commits"), style="yellow")
        )
        return

    # === כותרת ===
    console.print()
    console.print(
        Panel.fit(
            f"[{th('title')}]ContextPulse[/{th('title')}] - {t('report_title')}\n"
            f"[{th('subtitle')}]{period_label}[/{th('subtitle')}]",
            subtitle=f"{len(commits)} {t('commits_word')}",
            border_style=th("border"),
        )
    )

    # === סיכום טקסטואלי ===
    categories = group_by_category(commits)
    summary = generate_summary(commits, categories)
    console.print()
    console.print(Panel(summary, title=t("summary"), border_style=th("summary_border")))

    # === טבלת קומיטים ===
    console.print()
    table = Table(
        title=t("commits"),
        show_header=True,
        header_style=th("header"),
    )
    table.add_column("Date", style="dim", width=16)
    table.add_column("Hash", style=th("accent"), width=9)
    table.add_column("Message", style="white")
    table.add_column("Files", justify="right", style=th("positive"))

    for commit in commits:
        table.add_row(
            commit["date"],
            commit["hash"],
            commit["message"],
            str(commit["files_changed"]),
        )

    console.print(table)

    # === סיכום לפי קטגוריות עם צבעים ===
    console.print()
    cat_table = Table(
        title=t("changes_by_cat"),
        show_header=True,
        header_style="bold blue",
    )
    cat_table.add_column("Category", style="bold")
    cat_table.add_column(t("commits_word"), justify="right")
    cat_table.add_column("Files", justify="right")

    sorted_cats = sorted(
        categories.items(),
        key=lambda x: x[1]["commits"],
        reverse=True,
    )
    for cat_name, data in sorted_cats:
        color = CATEGORY_COLORS.get(cat_name, "white")
        cat_table.add_row(
            f"[{color}]{cat_name}[/{color}]",
            f"[{color}]{data['commits']}[/{color}]",
            f"[{color}]{len(data['files'])}[/{color}]",
        )

    console.print(cat_table)

    # === Hot Files ===
    display_hot_files(commits)

    # === פירוט לפי תיקיות (monorepo) ===
    display_directory_breakdown(commits)

    # === גרף פעילות יומי ===
    display_activity_chart(commits)

    # === Diff Summary — שורות שנוספו/נמחקו ===
    total_insertions = sum(c.get("insertions", 0) for c in commits)
    total_deletions = sum(c.get("deletions", 0) for c in commits)
    if total_insertions > 0 or total_deletions > 0:
        console.print()
        console.print(
            f"  [{th('positive')}]+{total_insertions} {t('lines_added')}[/{th('positive')}]  "
            f"[{th('negative')}]-{total_deletions} {t('lines_removed')}[/{th('negative')}]  "
            f"[{th('neutral')}]({t('net')}: {total_insertions - total_deletions:+d})[/{th('neutral')}]"
        )

    # === שורת סיכום ===
    total_files = sum(c["files_changed"] for c in commits)
    authors = set(c["author"] for c in commits)
    console.print()
    console.print(
        f"  [bold]{t('total')}:[/bold] {len(commits)} {t('commits_word')} "
        f"{t('by')} {len(authors)} {t('author_s')}, "
        f"{total_files} {t('file_changes')}"
    )
    console.print()


def export_json(commits, period_label):
    """
    מייצא את הדוח כ-JSON.
    JSON = פורמט אוניברסלי שכל תוכנה יכולה לקרוא.
    שימושי אם רוצים לחבר את ContextPulse לכלים אחרים.
    """
    categories = group_by_category(commits)
    hot = get_hot_files(commits)

    output = {
        "period": period_label,
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_commits": len(commits),
        "total_files": sum(c["files_changed"] for c in commits),
        "authors": list(set(c["author"] for c in commits)),
        "summary": generate_summary(commits, categories),
        "categories": {
            name: {"commits": d["commits"], "files": len(d["files"])}
            for name, d in categories.items()
        },
        "hot_files": [
            {"file": f, "changes": c} for f, c in hot
        ],
        "commits": [
            {
                "hash": c["hash"],
                "message": c["message"],
                "author": c["author"],
                "date": c["date"],
                "files_changed": c["files_changed"],
            }
            for c in commits
        ],
    }

    # indent=2 = הדפסה יפה עם רווחים (לא שורה אחת ארוכה)
    # ensure_ascii=False = תומך בעברית ותווים מיוחדים
    print(json.dumps(output, indent=2, ensure_ascii=False))


def export_markdown(commits, period_label, output_path):
    """מייצא את הדוח לקובץ Markdown."""
    categories = group_by_category(commits)
    total_files = sum(c["files_changed"] for c in commits)
    authors = set(c["author"] for c in commits)
    summary = generate_summary(commits, categories)
    hot = get_hot_files(commits)

    lines = []
    lines.append("# ContextPulse - Git Activity Report")
    lines.append(f"**Period:** {period_label}  ")
    lines.append(
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  "
    )
    lines.append("")

    lines.append("## Summary")
    lines.append(f"> {summary}")
    lines.append("")
    lines.append(f"- **Commits:** {len(commits)}")
    lines.append(f"- **Authors:** {', '.join(authors)}")
    lines.append(f"- **File changes:** {total_files}")
    lines.append("")

    lines.append("## Changes by Category")
    lines.append("| Category | Commits | Files |")
    lines.append("|----------|---------|-------|")
    sorted_cats = sorted(
        categories.items(),
        key=lambda x: x[1]["commits"],
        reverse=True,
    )
    for cat_name, data in sorted_cats:
        lines.append(
            f"| {cat_name} | {data['commits']} | {len(data['files'])} |"
        )
    lines.append("")

    # Hot Files
    if hot:
        lines.append("## Hot Files")
        lines.append("| # | File | Changes |")
        lines.append("|---|------|---------|")
        for i, (filename, count) in enumerate(hot, 1):
            lines.append(f"| {i} | `{filename}` | {count} |")
        lines.append("")

    # גרף פעילות
    day_counts = Counter(c["date_short"] for c in commits)
    if day_counts:
        lines.append("## Daily Activity")
        max_count = max(day_counts.values())
        for day, count in sorted(day_counts.items()):
            bar_len = round(count / max_count * 20)
            bar = "█" * bar_len
            lines.append(f"- `{day}` {bar} ({count})")
        lines.append("")

    lines.append("## Commits")
    lines.append("| Date | Hash | Message | Files |")
    lines.append("|------|------|---------|-------|")
    for commit in commits:
        lines.append(
            f"| {commit['date']} | `{commit['hash']}` "
            f"| {commit['message']} | {commit['files_changed']} |"
        )
    lines.append("")

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]Report saved to:[/green] {output_path}")


def interactive_mode():
    """
    מצב אינטראקטיבי — תפריט שמאפשר לבחור אפשרויות בלי לזכור דגלים.
    במקום לכתוב pulse --month --export report.md אתה פשוט בוחר מתפריט.
    """
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]ContextPulse[/bold cyan] - Interactive Mode",
            border_style="cyan",
        )
    )
    console.print()

    # שלב 1: בחירת ריפו
    repo_path = Prompt.ask(
        "Repository path",
        default=".",
    )

    # בדיקה שזה ריפו תקין
    try:
        Repo(repo_path)
    except (InvalidGitRepositoryError, NoSuchPathError):
        console.print(f"[red]Error:[/red] '{repo_path}' is not a Git repository.")
        return

    # שלב 2: בחירת טווח זמן
    console.print()
    console.print("[bold]Time range:[/bold]")
    console.print("  1. Today")
    console.print("  2. Last 3 days")
    console.print("  3. Last 7 days (week)")
    console.print("  4. Last 30 days (month)")
    console.print("  5. Custom number of days")
    console.print("  6. Since specific date")
    console.print()

    choice = Prompt.ask("Choose", choices=["1", "2", "3", "4", "5", "6"], default="3")

    if choice == "1":
        days, period_label = 1, "today"
    elif choice == "2":
        days, period_label = 3, "last 3 days"
    elif choice == "3":
        days, period_label = 7, "last 7 days"
    elif choice == "4":
        days, period_label = 30, "last 30 days"
    elif choice == "5":
        days = IntPrompt.ask("How many days back")
        period_label = f"last {days} days"
    elif choice == "6":
        date_str = Prompt.ask("Since date (YYYY-MM-DD)")
        try:
            since_dt = datetime.strptime(date_str, "%Y-%m-%d")
            days = (datetime.now() - since_dt).days
            period_label = f"since {date_str}"
        except ValueError:
            console.print("[red]Error:[/red] Invalid date format.")
            return

    # שלב 3: סינון לפי מחבר?
    console.print()
    author = Prompt.ask("Filter by author (leave empty for all)", default="")
    author_filter = author if author else None
    if author_filter:
        period_label += f" (author: {author_filter})"

    # שלב 4: הרצה
    console.print()
    commits = get_commits(repo_path, days, author_filter)
    display_report(commits, period_label)

    # שלב 5: ייצוא?
    console.print()
    export = Prompt.ask(
        "Export report? (md/json/no)",
        choices=["md", "json", "no"],
        default="no",
    )
    if export == "md":
        filename = Prompt.ask("Filename", default="report.md")
        export_markdown(commits, period_label, filename)
    elif export == "json":
        export_json(commits, period_label)


LOGO = """[bold cyan]
   ____            _            _   ____        _
  / ___|___  _ __ | |_ _____  _| |_|  _ \\ _   _| |___  ___
 | |   / _ \\| '_ \\| __/ _ \\ \\/ / __| |_) | | | | / __|/ _ \\
 | |__| (_) | | | | ||  __/>  <| |_|  __/| |_| | \\__ \\  __/
  \\____\\___/|_| |_|\\__\\___/_/\\_\\\\__|_|    \\__,_|_|___/\\___|
[/bold cyan][dim]  Turn your Git history into a human story[/dim]
"""


def show_logo():
    """מציג את הלוגו של ContextPulse."""
    console.print(LOGO)


def team_report(repo_path=".", days=30):
    """
    pulse team: מראה מי הכי פעיל בפרויקט.
    כולל: מספר קומיטים, אחוז תרומה, קבצים שהשתנו.
    """
    repo = Repo(repo_path)
    since_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

    # אוספים נתונים לכל מחבר
    authors = defaultdict(lambda: {
        "commits": 0, "files": set(), "first": None, "last": None,
    })

    for commit in repo.iter_commits():
        if commit.committed_date < since_date:
            break
        name = str(commit.author)
        authors[name]["commits"] += 1
        for f in commit.stats.files:
            authors[name]["files"].add(f)
        date_str = datetime.fromtimestamp(
            commit.committed_date
        ).strftime("%Y-%m-%d")
        if authors[name]["first"] is None:
            authors[name]["first"] = date_str
        authors[name]["last"] = date_str

    if not authors:
        console.print(Panel("No commits found.", style="yellow"))
        return

    show_logo()
    total_commits = sum(a["commits"] for a in authors.values())

    console.print(
        Panel.fit(
            f"[bold cyan]Team Report[/bold cyan] — last {days} days",
            subtitle=f"{len(authors)} contributor(s)",
        )
    )
    console.print()

    table = Table(
        title="Contributors",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Author", style="bold")
    table.add_column("Commits", justify="right", style="cyan")
    table.add_column("%", justify="right", style="green")
    table.add_column("Files", justify="right", style="yellow")
    table.add_column("Active", style="dim")

    sorted_authors = sorted(
        authors.items(),
        key=lambda x: x[1]["commits"],
        reverse=True,
    )

    for i, (name, data) in enumerate(sorted_authors, 1):
        pct = round(data["commits"] / total_commits * 100)
        bar = "█" * (pct // 5)  # בר ויזואלי
        active_range = data["last"]
        if data["first"] != data["last"]:
            active_range = f"{data['last']} → {data['first']}"
        table.add_row(
            str(i),
            name,
            str(data["commits"]),
            f"{pct}% {bar}",
            str(len(data["files"])),
            active_range,
        )

    console.print(table)
    console.print()


def hours_report(repo_path=".", days=30):
    """
    pulse hours: מנתח באילו שעות ובאילו ימים אתה הכי פעיל.
    עוזר להבין את דפוסי העבודה שלך.
    """
    repo = Repo(repo_path)
    since_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

    hour_counts = Counter()
    day_counts = Counter()

    for commit in repo.iter_commits():
        if commit.committed_date < since_date:
            break
        commit_dt = datetime.fromtimestamp(commit.committed_date)
        hour_counts[commit_dt.hour] += 1
        day_counts[commit_dt.strftime("%A")] += 1

    if not hour_counts:
        console.print(Panel("No commits found.", style="yellow"))
        return

    show_logo()
    console.print(
        Panel.fit(
            f"[bold cyan]Work Patterns[/bold cyan] — last {days} days",
        )
    )

    # === שעות ===
    console.print()
    console.print("[bold]Activity by Hour[/bold]")

    max_hour = max(hour_counts.values()) if hour_counts else 1

    for hour in range(24):
        count = hour_counts.get(hour, 0)
        bar_len = round(count / max_hour * 25) if count > 0 else 0
        bar = "█" * bar_len

        # צבע: כחול=לילה, צהוב=בוקר, ירוק=צהריים, אדום=ערב
        if 6 <= hour < 12:
            color = "yellow"
            period = "morning"
        elif 12 <= hour < 18:
            color = "green"
            period = "afternoon"
        elif 18 <= hour < 22:
            color = "red"
            period = "evening"
        else:
            color = "blue"
            period = "night"

        hour_str = f"{hour:02d}:00"
        if count > 0:
            console.print(
                f"  {hour_str}  [{color}]{bar}[/{color}] {count}"
            )
        else:
            console.print(f"  {hour_str}  [dim]·[/dim]")

    # === ימים ===
    console.print()
    console.print("[bold]Activity by Day[/bold]")

    day_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ]
    max_day = max(day_counts.values()) if day_counts else 1

    for day_name in day_order:
        count = day_counts.get(day_name, 0)
        bar_len = round(count / max_day * 25) if count > 0 else 0
        bar = "█" * bar_len
        short = day_name[:3]

        if count > 0:
            console.print(f"  {short}  [cyan]{bar}[/cyan] {count}")
        else:
            console.print(f"  {short}  [dim]·[/dim]")

    # === תובנות ===
    console.print()
    if hour_counts:
        peak_hour = max(hour_counts, key=hour_counts.get)
        console.print(
            f"  [bold]Peak hour:[/bold] {peak_hour:02d}:00 "
            f"({hour_counts[peak_hour]} commits)"
        )
    if day_counts:
        peak_day = max(day_counts, key=day_counts.get)
        console.print(
            f"  [bold]Peak day:[/bold] {peak_day} "
            f"({day_counts[peak_day]} commits)"
        )

    # זיהוי דפוס
    morning = sum(hour_counts.get(h, 0) for h in range(6, 12))
    afternoon = sum(hour_counts.get(h, 0) for h in range(12, 18))
    evening = sum(hour_counts.get(h, 0) for h in range(18, 22))
    night = sum(hour_counts.get(h, 0) for h in range(22, 24))
    night += sum(hour_counts.get(h, 0) for h in range(0, 6))

    periods = {
        "morning person (6-12)": morning,
        "afternoon coder (12-18)": afternoon,
        "evening hacker (18-22)": evening,
        "night owl (22-06)": night,
    }
    top_period = max(periods, key=periods.get)
    console.print(f"  [bold]Pattern:[/bold] You're a {top_period}")
    console.print()


def vs_report(repo_path=".", days=7):
    """
    pulse vs: משווה את התקופה הנוכחית לתקופה הקודמת.
    למשל: שבוע אחרון vs שבוע לפני.
    """
    repo = Repo(repo_path)

    now = datetime.now().timestamp()
    current_start = now - (days * 24 * 60 * 60)
    previous_start = current_start - (days * 24 * 60 * 60)

    current_commits = []
    previous_commits = []

    for commit in repo.iter_commits():
        if commit.committed_date < previous_start:
            break
        if commit.committed_date >= current_start:
            current_commits.append(commit)
        elif commit.committed_date >= previous_start:
            previous_commits.append(commit)

    show_logo()
    console.print(
        Panel.fit(
            f"[bold cyan]Period Comparison[/bold cyan]\n"
            f"[dim]Current {days} days vs previous {days} days[/dim]",
        )
    )
    console.print()

    # === טבלת השוואה ===
    table = Table(
        show_header=True,
        header_style="bold blue",
    )
    table.add_column("Metric", style="bold")
    table.add_column(f"Previous {days}d", justify="right")
    table.add_column(f"Current {days}d", justify="right")
    table.add_column("Change", justify="right")

    def change_str(current, previous):
        """מחשב את ההבדל ומסמן בצבע: ירוק=עלייה, אדום=ירידה."""
        if previous == 0:
            if current > 0:
                return "[green]+∞[/green]"
            return "[dim]—[/dim]"
        diff = current - previous
        pct = round((diff / previous) * 100)
        if diff > 0:
            return f"[green]+{diff} (+{pct}%)[/green]"
        elif diff < 0:
            return f"[red]{diff} ({pct}%)[/red]"
        return "[dim]same[/dim]"

    curr_count = len(current_commits)
    prev_count = len(previous_commits)
    curr_files = sum(len(c.stats.files) for c in current_commits)
    prev_files = sum(len(c.stats.files) for c in previous_commits)
    curr_authors = len(set(str(c.author) for c in current_commits))
    prev_authors = len(set(str(c.author) for c in previous_commits))

    table.add_row(
        "Commits",
        str(prev_count),
        str(curr_count),
        change_str(curr_count, prev_count),
    )
    table.add_row(
        "File changes",
        str(prev_files),
        str(curr_files),
        change_str(curr_files, prev_files),
    )
    table.add_row(
        "Contributors",
        str(prev_authors),
        str(curr_authors),
        change_str(curr_authors, prev_authors),
    )

    console.print(table)

    # === סיכום ===
    console.print()
    if curr_count > prev_count:
        console.print(
            f"  [green]↑ Productivity up![/green] "
            f"{curr_count} vs {prev_count} commits"
        )
    elif curr_count < prev_count:
        console.print(
            f"  [red]↓ Slower period.[/red] "
            f"{curr_count} vs {prev_count} commits"
        )
    else:
        console.print("  [dim]Same pace as before.[/dim]")
    console.print()


def scan_code(repo_path="."):
    """
    פקודת scan: מנתח את הקוד בריפו ומראה דוח מבנה + איכות.
    שימושי ללומדים שרוצים להבין פרויקט, ולמפתחים שרוצים לבדוק איכות.
    """
    try:
        repo = Repo(repo_path)
    except (InvalidGitRepositoryError, NoSuchPathError):
        console.print(f"[red]Error:[/red] '{repo_path}' is not a Git repository.")
        return

    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]ContextPulse[/bold cyan] - Code Scanner",
            border_style="cyan",
        )
    )

    # === סריקת כל הקבצים בריפו ===
    # repo.git.ls_files() = מחזיר את כל הקבצים שגיט עוקב אחריהם
    all_files = repo.git.ls_files().split("\n")
    all_files = [f for f in all_files if f]  # מסנן שורות ריקות

    # === סטטיסטיקות כלליות ===
    total_files = len(all_files)
    categories = Counter()
    file_sizes = {}

    for filepath in all_files:
        cat = get_category(filepath)
        categories[cat] += 1
        # בודקים גודל קובץ
        full_path = Path(repo_path) / filepath
        if full_path.exists():
            size = full_path.stat().st_size
            file_sizes[filepath] = size

    # === טבלת סוגי קבצים ===
    console.print()
    console.print(f"[bold]Project: {Path(repo_path).resolve().name}[/bold]")
    console.print(f"Total files tracked by Git: {total_files}")
    console.print()

    cat_table = Table(
        title="File Types in Project",
        show_header=True,
        header_style="bold blue",
    )
    cat_table.add_column("Type", style="bold")
    cat_table.add_column("Files", justify="right", style="cyan")
    cat_table.add_column("%", justify="right", style="green")

    for cat_name, count in categories.most_common():
        color = CATEGORY_COLORS.get(cat_name, "white")
        pct = round(count / total_files * 100)
        cat_table.add_row(
            f"[{color}]{cat_name}[/{color}]",
            f"[{color}]{count}[/{color}]",
            f"[{color}]{pct}%[/{color}]",
        )

    console.print(cat_table)

    # === הקבצים הכי גדולים ===
    if file_sizes:
        console.print()
        big_table = Table(
            title="Largest Files",
            show_header=True,
            header_style="bold red",
        )
        big_table.add_column("#", style="dim", width=3)
        big_table.add_column("File", style="white")
        big_table.add_column("Size", justify="right", style="yellow")

        sorted_sizes = sorted(
            file_sizes.items(), key=lambda x: x[1], reverse=True
        )
        for i, (filepath, size) in enumerate(sorted_sizes[:10], 1):
            if size >= 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.1f} MB"
            elif size >= 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            big_table.add_row(str(i), filepath, size_str)

        console.print(big_table)

    # === בדיקות איכות ===
    console.print()
    console.print("[bold]Quality Check[/bold]")
    issues = []
    suggestions = []

    # בדיקה 1: האם יש README?
    has_readme = any(f.lower().startswith("readme") for f in all_files)
    if has_readme:
        console.print("  [green]✓[/green] README found")
    else:
        console.print("  [red]✗[/red] No README file")
        issues.append("Add a README.md to explain your project")

    # בדיקה 2: האם יש .gitignore?
    has_gitignore = ".gitignore" in all_files
    if has_gitignore:
        console.print("  [green]✓[/green] .gitignore found")
    else:
        console.print("  [red]✗[/red] No .gitignore file")
        issues.append("Add .gitignore to avoid tracking unnecessary files")

    # בדיקה 3: האם יש בדיקות?
    test_files = [f for f in all_files if "test" in f.lower()]
    if test_files:
        console.print(f"  [green]✓[/green] Tests found ({len(test_files)} test files)")
    else:
        console.print("  [yellow]![/yellow] No test files found")
        suggestions.append("Consider adding tests to catch bugs early")

    # בדיקה 4: האם יש requirements.txt או pyproject.toml?
    has_deps = any(
        f in all_files
        for f in ["requirements.txt", "pyproject.toml", "setup.py", "package.json"]
    )
    if has_deps:
        console.print("  [green]✓[/green] Dependency file found")
    else:
        console.print("  [yellow]![/yellow] No dependency file found")
        suggestions.append("Add requirements.txt or pyproject.toml")

    # בדיקה 5: האם יש LICENSE?
    has_license = any(f.lower().startswith("license") for f in all_files)
    if has_license:
        console.print("  [green]✓[/green] LICENSE found")
    else:
        console.print("  [yellow]![/yellow] No LICENSE file")
        suggestions.append("Add a LICENSE file (MIT is a good default)")

    # בדיקה 6: קבצים גדולים מדי
    big_files = [
        f for f, s in file_sizes.items()
        if s > 1024 * 1024  # יותר מ-1MB
    ]
    if big_files:
        console.print(
            f"  [yellow]![/yellow] {len(big_files)} files larger than 1MB"
        )
        suggestions.append(
            "Large files slow down Git. Consider Git LFS for big files"
        )
    else:
        console.print("  [green]✓[/green] No oversized files")

    # === מבנה התיקיות ===
    console.print()
    dirs = set()
    for f in all_files:
        parts = Path(f).parts
        if len(parts) > 1:
            dirs.add(parts[0])

    if dirs:
        console.print("[bold]Project Structure[/bold]")
        for d in sorted(dirs):
            dir_files = [f for f in all_files if f.startswith(d + "/")]
            console.print(f"  [cyan]{d}/[/cyan] ({len(dir_files)} files)")

        root_files = [f for f in all_files if "/" not in f]
        if root_files:
            console.print(f"  [dim](root)[/dim] ({len(root_files)} files)")

    # === סיכום ===
    console.print()
    score = 0
    checks = 6
    if has_readme:
        score += 1
    if has_gitignore:
        score += 1
    if test_files:
        score += 1
    if has_deps:
        score += 1
    if has_license:
        score += 1
    if not big_files:
        score += 1

    if score == checks:
        color = "green"
        grade = "Excellent!"
    elif score >= 4:
        color = "cyan"
        grade = "Good"
    elif score >= 2:
        color = "yellow"
        grade = "Needs work"
    else:
        color = "red"
        grade = "Needs attention"

    console.print(
        Panel(
            f"[{color}]Score: {score}/{checks} — {grade}[/{color}]",
            title="Project Health",
            border_style=color,
        )
    )

    if issues:
        console.print()
        console.print("[bold red]Issues:[/bold red]")
        for issue in issues:
            console.print(f"  [red]•[/red] {issue}")

    if suggestions:
        console.print()
        console.print("[bold yellow]Suggestions:[/bold yellow]")
        for sug in suggestions:
            console.print(f"  [yellow]•[/yellow] {sug}")

    console.print()


def multi_report(base_path=".", days=7):
    """
    pulse multi: סורק כמה ריפו ביחד ומציג סיכום משולב.
    מחפש את כל תיקיות ה-Git בתוך הנתיב שניתן.
    למשל: pulse multi ~/code → סורק את כל הפרויקטים בתוך ~/code
    """
    base = Path(base_path).resolve()

    if not base.is_dir():
        console.print(f"[red]Error:[/red] '{base_path}' is not a directory.")
        return

    # מחפשים תיקיות .git
    repos = []
    for item in sorted(base.iterdir()):
        if item.is_dir() and (item / ".git").exists():
            repos.append(item)

    if not repos:
        console.print(
            f"[yellow]No Git repositories found in {base_path}[/yellow]"
        )
        return

    show_logo()
    console.print(
        Panel.fit(
            f"[bold cyan]Multi-Repo Report[/bold cyan]\n"
            f"[dim]{base} — last {days} days[/dim]",
            subtitle=f"{len(repos)} repositories",
        )
    )
    console.print()

    table = Table(
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Repository", style="bold")
    table.add_column("Commits", justify="right", style="cyan")
    table.add_column("Files", justify="right", style="green")
    table.add_column("+Lines", justify="right", style="green")
    table.add_column("-Lines", justify="right", style="red")
    table.add_column("Last Commit", style="dim")

    total_commits = 0
    total_files = 0

    for repo_path in repos:
        try:
            commits = get_commits(str(repo_path), days)
            commit_count = len(commits)
            file_count = sum(c["files_changed"] for c in commits)
            ins = sum(c.get("insertions", 0) for c in commits)
            dels = sum(c.get("deletions", 0) for c in commits)
            last = commits[0]["date_short"] if commits else "—"
            total_commits += commit_count
            total_files += file_count

            # צבע לפי פעילות
            name = repo_path.name
            if commit_count == 0:
                name = f"[dim]{name}[/dim]"

            table.add_row(
                name,
                str(commit_count) if commit_count > 0 else "[dim]—[/dim]",
                str(file_count) if file_count > 0 else "[dim]—[/dim]",
                f"+{ins}" if ins > 0 else "[dim]—[/dim]",
                f"-{dels}" if dels > 0 else "[dim]—[/dim]",
                last,
            )
        except Exception:
            table.add_row(
                repo_path.name, "[red]error[/red]", "", "", "", ""
            )

    console.print(table)
    console.print()
    console.print(
        f"  [bold]Total:[/bold] {total_commits} commits across "
        f"{len(repos)} repos, {total_files} file changes"
    )
    console.print()


def init_config(repo_path="."):
    """
    pulse init: יוצר קובץ .pulserc בריפו עם הגדרות ברירת מחדל.
    ככה לא צריך לכתוב --days 30 כל פעם — הגדרות נשמרות לפרויקט.
    """
    config_path = Path(repo_path) / ".pulserc"

    if config_path.exists():
        console.print(
            f"[yellow].pulserc already exists in {repo_path}[/yellow]"
        )
        console.print("Edit it manually or delete it to recreate.")
        return

    default_config = """# ContextPulse Configuration
# This file sets default options for this repository.
# Delete any line to use the global default.

# How many days to look back (default: 7)
days = 7

# Default export format: none, md, json
export = none

# Show logo: true, false
logo = true
"""

    config_path.write_text(default_config, encoding="utf-8")
    console.print(f"[green]Created .pulserc in {repo_path}[/green]")
    console.print("Edit it to set your preferred defaults for this project.")
    console.print()
    console.print("[dim]Tip: Add .pulserc to .gitignore if you don't want "
                  "to share your settings.[/dim]")


def streak_report(repo_path="."):
    """
    pulse streak: מראה כמה ימים רצופים אתה עושה קומיטים.
    כמו streak ב-GitHub — מוטיבציה להמשיך!
    """
    repo = Repo(repo_path)

    # אוספים את כל הימים שהיו בהם קומיטים
    commit_days = set()
    for commit in repo.iter_commits():
        day = datetime.fromtimestamp(
            commit.committed_date
        ).strftime("%Y-%m-%d")
        commit_days.add(day)

    if not commit_days:
        console.print(Panel("No commits found.", style="yellow"))
        return

    # ממיינים ובודקים רצף מהיום אחורה
    today = datetime.now().strftime("%Y-%m-%d")
    current_streak = 0
    check_date = datetime.now()

    while True:
        day_str = check_date.strftime("%Y-%m-%d")
        if day_str in commit_days:
            current_streak += 1
            check_date = check_date.replace(
                hour=0, minute=0, second=0
            ) - __import__("datetime").timedelta(days=1)
        else:
            # אם היום אין קומיט, בודקים אם אתמול היה
            if current_streak == 0 and day_str == today:
                check_date = check_date.replace(
                    hour=0, minute=0, second=0
                ) - __import__("datetime").timedelta(days=1)
                continue
            break

    # מוצאים את הרצף הכי ארוך אי פעם
    sorted_days = sorted(commit_days)
    best_streak = 0
    temp_streak = 1

    for i in range(1, len(sorted_days)):
        prev = datetime.strptime(sorted_days[i - 1], "%Y-%m-%d")
        curr = datetime.strptime(sorted_days[i], "%Y-%m-%d")
        if (curr - prev).days == 1:
            temp_streak += 1
        else:
            best_streak = max(best_streak, temp_streak)
            temp_streak = 1
    best_streak = max(best_streak, temp_streak)

    # תצוגה
    show_logo()
    console.print()

    # אש לפי רצף
    if current_streak >= 30:
        fire = "🔥🔥🔥"
        msg = "LEGENDARY!"
    elif current_streak >= 14:
        fire = "🔥🔥"
        msg = "On fire!"
    elif current_streak >= 7:
        fire = "🔥"
        msg = "Great streak!"
    elif current_streak >= 3:
        fire = "✨"
        msg = "Building momentum!"
    elif current_streak >= 1:
        fire = "👍"
        msg = "Keep going!"
    else:
        fire = "💤"
        msg = "Start a new streak today!"

    console.print(
        Panel(
            f"{fire} [bold]Current streak: {current_streak} days[/bold] {fire}\n"
            f"[dim]{msg}[/dim]\n\n"
            f"Best streak ever: [cyan]{best_streak} days[/cyan]\n"
            f"Total active days: [green]{len(commit_days)}[/green]",
            title="Commit Streak",
            border_style="yellow",
        )
    )

    # לוח שנה של 4 שבועות אחרונים
    console.print()
    console.print("[bold]Last 28 days:[/bold]")
    line = "  "
    for i in range(27, -1, -1):
        day = datetime.now() - __import__("datetime").timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        if day_str in commit_days:
            line += "[green]■[/green] "
        else:
            line += "[dim]□[/dim] "
        if (28 - i) % 7 == 0:
            line += " "
    console.print(line)
    console.print("  [dim]■ = committed  □ = no commits[/dim]")
    console.print()


def pretty_log(repo_path=".", count=20):
    """
    pulse log: git log אבל יפה — עם צבעים, קטגוריות וסיכום.
    כברירת מחדל מראה 20 קומיטים אחרונים.
    """
    repo = Repo(repo_path)

    show_logo()
    console.print(
        Panel.fit(
            f"[{th('title')}]Recent Commits[/{th('title')}]",
            border_style=th("border"),
        )
    )
    console.print()

    for i, commit in enumerate(repo.iter_commits(max_count=count)):
        commit_dt = datetime.fromtimestamp(commit.committed_date)
        date_str = commit_dt.strftime("%Y-%m-%d %H:%M")
        msg = commit.message.strip().split("\n")[0]
        hash_short = commit.hexsha[:7]
        author = str(commit.author)
        files = list(commit.stats.files.keys())
        ins = commit.stats.total.get("insertions", 0)
        dels = commit.stats.total.get("deletions", 0)

        # סוג פעולה לפי הודעת הקומיט
        msg_lower = msg.lower()
        if msg_lower.startswith("fix"):
            icon = "🔧"
        elif msg_lower.startswith("add"):
            icon = "✨"
        elif msg_lower.startswith("update") or msg_lower.startswith("improve"):
            icon = "📦"
        elif msg_lower.startswith("refactor"):
            icon = "♻️"
        elif msg_lower.startswith("remove") or msg_lower.startswith("delete"):
            icon = "🗑️"
        elif msg_lower.startswith("test"):
            icon = "🧪"
        elif msg_lower.startswith("doc"):
            icon = "📝"
        else:
            icon = "💻"

        console.print(
            f"  [{th('accent')}]{hash_short}[/{th('accent')}] "
            f"[dim]{date_str}[/dim] {icon} {msg}"
        )
        console.print(
            f"           [dim]{author} · "
            f"{len(files)} files · "
            f"[green]+{ins}[/green] [red]-{dels}[/red][/dim]"
        )
        if i < count - 1:
            console.print("           [dim]│[/dim]")

    console.print()


def show_help():
    """
    pulse help: מדריך יפה עם כל הפקודות — הרבה יותר נחמד מ---help.
    """
    show_logo()

    # פקודות ראשיות
    console.print("[bold]Commands:[/bold]")
    cmds = Table(show_header=False, box=None, padding=(0, 2))
    cmds.add_column(style="cyan bold", width=22)
    cmds.add_column(style="white")

    cmds.add_row("pulse", "Weekly activity report (default)")
    cmds.add_row("pulse today", "Today's commits only")
    cmds.add_row("pulse week", "Last 7 days")
    cmds.add_row("pulse month", "Last 30 days")
    cmds.add_row("pulse since DATE", "Since a specific date (YYYY-MM-DD)")
    cmds.add_row("pulse scan", "Project health check + quality score")
    cmds.add_row("pulse team", "Top contributors breakdown")
    cmds.add_row("pulse hours", "Work patterns (hours & days)")
    cmds.add_row("pulse vs", "Compare current vs previous period")
    cmds.add_row("pulse streak", "Commit streak + calendar")
    cmds.add_row("pulse log", "Pretty git log with icons")
    cmds.add_row("pulse multi PATH", "Scan all repos in a directory")
    cmds.add_row("pulse init", "Create .pulserc config file")
    cmds.add_row("pulse i", "Interactive mode (guided menu)")
    cmds.add_row("pulse help", "This help page")
    console.print(cmds)

    # אפשרויות
    console.print()
    console.print("[bold]Options:[/bold]")
    opts = Table(show_header=False, box=None, padding=(0, 2))
    opts.add_column(style="yellow bold", width=22)
    opts.add_column(style="white")

    opts.add_row("--days N, -d N", "Look back N days")
    opts.add_row("--author NAME, -a", "Filter by author")
    opts.add_row("--compare A..B, -c", "Compare two branches")
    opts.add_row("--export FILE, -e", "Export to Markdown")
    opts.add_row("--html FILE", "Export to HTML with charts")
    opts.add_row("--json, -j", "Output as JSON")
    opts.add_row("--lang he, -l he", "Hebrew output")
    opts.add_row("--theme NAME", "Color theme (ocean/forest/sunset/minimal)")
    opts.add_row("--version, -v", "Show version")
    console.print(opts)

    # דוגמאות
    console.print()
    console.print("[bold]Examples:[/bold]")
    console.print("  [dim]$[/dim] pulse month --lang he")
    console.print("  [dim]$[/dim] pulse --theme ocean --export report.md")
    console.print("  [dim]$[/dim] pulse team 90 ~/code/my-project")
    console.print("  [dim]$[/dim] pulse multi ~/code")
    console.print("  [dim]$[/dim] pulse vs 14")
    console.print()


def export_html(commits, period_label, output_path):
    """
    מייצא דוח HTML עם טבלאות ו-CSS מעוצב.
    אפשר לפתוח בדפדפן — נראה הרבה יותר טוב מ-Markdown.
    """
    categories = group_by_category(commits)
    total_files = sum(c["files_changed"] for c in commits)
    total_ins = sum(c.get("insertions", 0) for c in commits)
    total_dels = sum(c.get("deletions", 0) for c in commits)
    authors = set(c["author"] for c in commits)
    summary = generate_summary(commits, categories)
    hot = get_hot_files(commits)
    day_counts = Counter(c["date_short"] for c in commits)

    # בניית גרף בר פשוט ב-CSS
    max_day = max(day_counts.values()) if day_counts else 1
    bars_html = ""
    for day, count in sorted(day_counts.items()):
        pct = round(count / max_day * 100)
        bars_html += (
            f'<div class="bar-row">'
            f'<span class="bar-label">{day}</span>'
            f'<div class="bar" style="width:{pct}%">{count}</div>'
            f'</div>\n'
        )

    # קטגוריות HTML
    cat_rows = ""
    sorted_cats = sorted(
        categories.items(), key=lambda x: x[1]["commits"], reverse=True
    )
    for cat_name, data in sorted_cats:
        cat_rows += (
            f"<tr><td>{cat_name}</td>"
            f"<td>{data['commits']}</td>"
            f"<td>{len(data['files'])}</td></tr>\n"
        )

    # Hot files HTML
    hot_rows = ""
    for i, (filename, count) in enumerate(hot, 1):
        fire = "🔥 " if count >= 5 else ""
        hot_rows += (
            f"<tr><td>{i}</td>"
            f"<td>{fire}{filename}</td>"
            f"<td>{count}</td></tr>\n"
        )

    # קומיטים HTML
    commit_rows = ""
    for c in commits:
        commit_rows += (
            f"<tr><td>{c['date']}</td>"
            f"<td><code>{c['hash']}</code></td>"
            f"<td>{c['message']}</td>"
            f"<td>+{c.get('insertions',0)}/-{c.get('deletions',0)}</td>"
            f"<td>{c['files_changed']}</td></tr>\n"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ContextPulse Report — {period_label}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0d1117; color: #c9d1d9; padding: 2rem; max-width: 960px; margin: auto; }}
  h1 {{ color: #58a6ff; margin-bottom: 0.5rem; }}
  h2 {{ color: #58a6ff; margin: 2rem 0 1rem; border-bottom: 1px solid #21262d; padding-bottom: 0.5rem; }}
  .summary {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px;
              padding: 1rem; margin: 1rem 0; }}
  .stats {{ display: flex; gap: 2rem; margin: 1rem 0; }}
  .stat {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px;
           padding: 1rem; text-align: center; flex: 1; }}
  .stat .number {{ font-size: 2rem; font-weight: bold; color: #58a6ff; }}
  .stat .label {{ color: #8b949e; font-size: 0.85rem; }}
  .green {{ color: #3fb950; }}
  .red {{ color: #f85149; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
  th {{ background: #161b22; color: #58a6ff; text-align: left; padding: 0.75rem; }}
  td {{ padding: 0.75rem; border-bottom: 1px solid #21262d; }}
  tr:hover {{ background: #161b22; }}
  code {{ background: #1f2937; padding: 2px 6px; border-radius: 3px; font-size: 0.9rem; }}
  .bar-row {{ display: flex; align-items: center; margin: 0.3rem 0; }}
  .bar-label {{ width: 100px; font-size: 0.85rem; color: #8b949e; }}
  .bar {{ background: linear-gradient(90deg, #238636, #3fb950); color: white;
          padding: 4px 8px; border-radius: 3px; font-size: 0.8rem; min-width: 30px; }}
  .footer {{ margin-top: 3rem; color: #484f58; font-size: 0.8rem; text-align: center; }}
</style>
</head>
<body>
<h1>ContextPulse</h1>
<p style="color:#8b949e">{period_label} — generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<div class="summary">{summary}</div>

<div class="stats">
  <div class="stat"><div class="number">{len(commits)}</div><div class="label">Commits</div></div>
  <div class="stat"><div class="number">{len(authors)}</div><div class="label">Authors</div></div>
  <div class="stat"><div class="number">{total_files}</div><div class="label">File Changes</div></div>
  <div class="stat"><div class="number green">+{total_ins}</div><div class="label">Lines Added</div></div>
  <div class="stat"><div class="number red">-{total_dels}</div><div class="label">Lines Removed</div></div>
</div>

<h2>Daily Activity</h2>
{bars_html}

<h2>Changes by Category</h2>
<table><tr><th>Category</th><th>Commits</th><th>Files</th></tr>
{cat_rows}</table>

<h2>Hot Files</h2>
<table><tr><th>#</th><th>File</th><th>Changes</th></tr>
{hot_rows}</table>

<h2>Commits</h2>
<table><tr><th>Date</th><th>Hash</th><th>Message</th><th>+/-</th><th>Files</th></tr>
{commit_rows}</table>

<div class="footer">Generated by ContextPulse v0.6.0 — pip install contextpulse</div>
</body></html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    console.print(f"[green]HTML report saved to:[/green] {output_path}")


# === מיפוי קיצורים עצלניים ===
# במקום pulse --today אפשר לכתוב pulse today
# המילון הזה מתרגם את המילה הקצרה לדגל המלא
SHORTCUTS = {
    "today": ["--today"],
    "t": ["--today"],
    "week": ["--week"],
    "w": ["--week"],
    "month": ["--month"],
    "m": ["--month"],
    "since": None,       # מטופל מיוחד — צריך תאריך אחריו
    "s": None,
    "json": ["--json"],
    "j": ["--json"],
    "interactive": ["--interactive"],
    "i": ["--interactive"],
    "scan": None,        # פקודה מיוחדת — ניתוח קוד
    "team": None,        # פקודה מיוחדת — דוח צוות
    "hours": None,       # פקודה מיוחדת — דפוסי עבודה
    "vs": None,          # פקודה מיוחדת — השוואת תקופות
    "multi": None,       # פקודה מיוחדת — ריבוי ריפו
    "init": None,        # פקודה מיוחדת — הגדרות לפרויקט
    "streak": None,      # פקודה מיוחדת — רצף ימים
    "log": None,         # פקודה מיוחדת — git log יפה
    "help": None,        # פקודה מיוחדת — מדריך
}


def expand_shortcuts(argv):
    """
    מתרגם קיצורים לדגלים מלאים.
    למשל: ["today"] → ["--today"]
           ["since", "2026-03-01"] → ["--since", "2026-03-01"]
           ["scan"] → מפעיל scan_code ומחזיר None
    """
    if not argv:
        return argv

    first = argv[0]

    # פקודות מיוחדות — כל אחת מפעילה פונקציה ייעודית
    if first == "scan":
        repo = argv[1] if len(argv) > 1 else "."
        scan_code(repo)
        return None

    if first == "team":
        repo = argv[1] if len(argv) > 1 else "."
        days = 30
        # אפשר pulse team 90 (לשנות ימים)
        if len(argv) > 1 and argv[1].isdigit():
            days = int(argv[1])
            repo = argv[2] if len(argv) > 2 else "."
        team_report(repo, days)
        return None

    if first == "hours":
        repo = argv[1] if len(argv) > 1 else "."
        days = 30
        if len(argv) > 1 and argv[1].isdigit():
            days = int(argv[1])
            repo = argv[2] if len(argv) > 2 else "."
        hours_report(repo, days)
        return None

    if first == "vs":
        days = 7
        repo = "."
        if len(argv) > 1 and argv[1].isdigit():
            days = int(argv[1])
            repo = argv[2] if len(argv) > 2 else "."
        elif len(argv) > 1:
            repo = argv[1]
        vs_report(repo, days)
        return None

    if first == "multi":
        path = argv[1] if len(argv) > 1 else "."
        days = 7
        if len(argv) > 2 and argv[2].isdigit():
            days = int(argv[2])
        multi_report(path, days)
        return None

    if first == "init":
        repo = argv[1] if len(argv) > 1 else "."
        init_config(repo)
        return None

    if first == "streak":
        repo = argv[1] if len(argv) > 1 else "."
        streak_report(repo)
        return None

    if first == "log":
        repo = "."
        count = 20
        if len(argv) > 1 and argv[1].isdigit():
            count = int(argv[1])
            repo = argv[2] if len(argv) > 2 else "."
        elif len(argv) > 1:
            repo = argv[1]
        pretty_log(repo, count)
        return None

    if first == "help":
        show_help()
        return None

    # since/s = צריך את התאריך שאחריו
    if first in ("since", "s") and len(argv) > 1:
        return ["--since", argv[1]] + argv[2:]

    # קיצור רגיל
    if first in SHORTCUTS and SHORTCUTS[first] is not None:
        return SHORTCUTS[first] + argv[1:]

    return argv


def main():
    """הפונקציה הראשית."""

    # === תרגום קיצורים ===
    # sys.argv[1:] = מה שהמשתמש כתב אחרי "pulse"
    # למשל: pulse today → sys.argv = ["pulse", "today"] → [1:] = ["today"]
    expanded = expand_shortcuts(sys.argv[1:])
    if expanded is None:
        return  # scan כבר רץ

    parser = argparse.ArgumentParser(
        prog="pulse",
        description="ContextPulse - Turn your Git history into a human story.",
    )
    parser.add_argument(
        "repo",
        nargs="?",
        default=".",
        help="Path to Git repository (default: current directory)",
    )

    # === קיצורי זמן ===
    time_group = parser.add_mutually_exclusive_group()
    time_group.add_argument(
        "--today", "-t",
        action="store_true",
        help="Show today's commits only",
    )
    time_group.add_argument(
        "--days", "-d",
        type=int,
        default=None,
        help="Number of days to look back (e.g., --days 3)",
    )
    time_group.add_argument(
        "--week", "-w",
        action="store_true",
        help="Last 7 days (this is the default)",
    )
    time_group.add_argument(
        "--month", "-m",
        action="store_true",
        help="Last 30 days",
    )
    time_group.add_argument(
        "--since", "-s",
        type=str,
        default=None,
        help="From a specific date (e.g., --since 2026-03-01)",
    )

    parser.add_argument(
        "--author", "-a",
        type=str,
        default=None,
        help="Filter by author name (e.g., --author 'John')",
    )
    parser.add_argument(
        "--export", "-e",
        type=str,
        default=None,
        help="Export report to Markdown file (e.g., report.md)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON (for integrating with other tools)",
    )
    parser.add_argument(
        "--compare", "-c",
        type=str,
        default=None,
        help="Compare two branches (e.g., --compare main..dev)",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode - choose options from a menu",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="ContextPulse 0.6.0",
    )
    parser.add_argument(
        "--html",
        type=str,
        default=None,
        help="Export report to HTML file (e.g., report.html)",
    )
    parser.add_argument(
        "--lang", "-l",
        type=str,
        default="en",
        choices=["en", "he"],
        help="Output language: en (English) or he (Hebrew)",
    )
    parser.add_argument(
        "--theme",
        type=str,
        default="default",
        choices=list(THEMES.keys()),
        help="Color theme: default, ocean, forest, sunset, minimal",
    )

    args = parser.parse_args(expanded)

    # === הגדרת שפה ו-theme ===
    global current_lang, current_theme
    current_lang = args.lang
    current_theme = THEMES.get(args.theme, THEMES["default"])

    # === מצב אינטראקטיבי ===
    if args.interactive:
        interactive_mode()
        return

    # === חישוב כמה ימים אחורה ===
    if args.today:
        days = 1
        period_label = "today"
    elif args.days is not None:
        days = args.days
        period_label = f"last {days} days"
    elif args.month:
        days = 30
        period_label = "last 30 days"
    elif args.since:
        try:
            since_dt = datetime.strptime(args.since, "%Y-%m-%d")
            days = (datetime.now() - since_dt).days
            period_label = f"since {args.since}"
        except ValueError:
            console.print(
                "[red]Error:[/red] Date format must be YYYY-MM-DD "
                "(e.g., 2026-03-01)"
            )
            return
    else:
        days = 7
        period_label = "last 7 days"

    if args.author:
        period_label += f" (author: {args.author})"

    # === הודעות שגיאה ברורות ===
    try:
        if args.compare:
            period_label = f"comparing {args.compare}"
            commits = get_compare_commits(args.repo, args.compare)
        else:
            commits = get_commits(args.repo, days, args.author)
    except InvalidGitRepositoryError:
        console.print(
            Panel(
                f"[red]'{args.repo}' is not a Git repository.[/red]\n\n"
                "Make sure you're inside a Git project, or specify a path:\n"
                "  [cyan]pulse ~/code/my-project[/cyan]\n\n"
                "To create a new Git repo here:\n"
                "  [cyan]git init[/cyan]",
                title="Not a Git Repository",
                border_style="red",
            )
        )
        return
    except NoSuchPathError:
        console.print(
            Panel(
                f"[red]Path '{args.repo}' does not exist.[/red]\n\n"
                "Check the path and try again.",
                title="Path Not Found",
                border_style="red",
            )
        )
        return

    # === הצגה ===
    if args.json:
        export_json(commits, period_label)
    else:
        show_logo()
        display_report(commits, period_label)

        if args.export:
            export_markdown(commits, period_label, args.export)
        if args.html:
            export_html(commits, period_label, args.html)


if __name__ == "__main__":
    main()
