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
            Panel("No commits found in this period.", style="yellow")
        )
        return

    # === כותרת ===
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]ContextPulse[/bold cyan] - Git Activity Report\n"
            f"[dim]{period_label}[/dim]",
            subtitle=f"{len(commits)} commits",
        )
    )

    # === סיכום טקסטואלי ===
    categories = group_by_category(commits)
    summary = generate_summary(commits, categories)
    console.print()
    console.print(Panel(summary, title="Summary", border_style="green"))

    # === טבלת קומיטים ===
    console.print()
    table = Table(
        title="Commits",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Date", style="dim", width=16)
    table.add_column("Hash", style="cyan", width=9)
    table.add_column("Message", style="white")
    table.add_column("Files", justify="right", style="green")

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
        title="Changes by Category",
        show_header=True,
        header_style="bold blue",
    )
    cat_table.add_column("Category", style="bold")
    cat_table.add_column("Commits", justify="right")
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

    # === שורת סיכום ===
    total_files = sum(c["files_changed"] for c in commits)
    authors = set(c["author"] for c in commits)
    console.print()
    console.print(
        f"  [bold]Total:[/bold] {len(commits)} commits by "
        f"{len(authors)} author(s), {total_files} file changes"
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

    args = parser.parse_args(expanded)

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


if __name__ == "__main__":
    main()
