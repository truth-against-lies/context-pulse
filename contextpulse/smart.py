"""
ContextPulse - Smart shortcuts, expand_shortcuts(), and interactive_mode().
"""

from datetime import datetime

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError
from rich.prompt import Prompt, IntPrompt

from .git_utils import get_commits
from .reports import display_report
from .export import export_markdown, export_json
from .scan import (
    scan_code, multi_report, init_config, learn_report,
    changelog_report, install_hook,
)
from .reports import (
    team_report, hours_report, vs_report, streak_report,
    pretty_log, trends_report, diff_report, blame_report,
    standup_report, id_report, commit_quality_report, code_age_report,
    watch_dashboard,
)
from .ui import console, show_help


# === Lazy shortcut mapping ===
SHORTCUTS = {
    "today": ["--today"],
    "t": ["--today"],
    "week": ["--week"],
    "w": ["--week"],
    "month": ["--month"],
    "m": ["--month"],
    "since": None,
    "s": None,
    "json": ["--json"],
    "j": ["--json"],
    "interactive": ["--interactive"],
    "i": ["--interactive"],
    "scan": None,
    "team": None,
    "hours": None,
    "vs": None,
    "multi": None,
    "init": None,
    "streak": None,
    "log": None,
    "trends": None,
    "learn": None,
    "diff": None,
    "blame": None,
    "standup": None,
    "id": None,
    "quality": None,
    "age": None,
    "changelog": None,
    "hook": None,
    "watch": None,
    "help": None,
    # === Hebrew shortcuts ===
    "היום": ["--today"],
    "שבוע": ["--week"],
    "חודש": ["--month"],
    "צוות": None,
    "שעות": None,
    "לימוד": None,
    "מגמות": None,
    "רצף": None,
    "סריקה": None,
    "השוואה": None,
    "לוג": None,
    "שינויים": None,
    "בעלות": None,
    "סטנדאפ": None,
    "זהות": None,
    "איכות": None,
    "גיל": None,
    "שינויון": None,     # = changelog
    "הוק": None,         # = hook
    "צפייה": None,       # = watch
    "עזרה": None,
}


def expand_shortcuts(argv):
    """
    Translates shortcuts to full flags.
    E.g.: ["today"] -> ["--today"]
          ["since", "2026-03-01"] -> ["--since", "2026-03-01"]
          ["scan"] -> runs scan_code and returns None
    """
    if not argv:
        return argv

    first = argv[0]

    # === Hebrew to English translation ===
    hebrew_to_english = {
        "צוות": "team", "שעות": "hours", "לימוד": "learn",
        "מגמות": "trends", "רצף": "streak", "סריקה": "scan",
        "השוואה": "vs", "לוג": "log", "שינויים": "diff",
        "בעלות": "blame", "סטנדאפ": "standup", "זהות": "id",
        "איכות": "quality", "גיל": "age",
        "שינויון": "changelog", "הוק": "hook", "צפייה": "watch",
        "עזרה": "help",
    }
    if first in hebrew_to_english:
        first = hebrew_to_english[first]
        argv[0] = first

    # === Smart Mode ===
    all_commands = set(SHORTCUTS.keys()) | set(hebrew_to_english.keys())
    if first not in all_commands and not first.startswith("-") and not first.startswith("/"):
        all_words = " ".join(argv).lower()

        # === Direct keywords ===
        SMART_KEYWORDS = {
            "learn": "learn", "לימוד": "learn", "code guide": "learn",
            "ללמוד": "learn", "קוד": "learn", "להבין": "learn",
            "guide": "learn", "מדריך": "learn", "tutorial": "learn",
            "team": "team", "צוות": "team", "contributors": "team",
            "תורמים": "team", "מי עבד": "team", "who worked": "team",
            "who contributed": "team", "מי תרם": "team",
            "hours": "hours", "שעות": "hours", "patterns": "hours",
            "דפוסים": "hours", "זמנים": "hours", "מתי עבדתי": "hours",
            "when did i work": "hours", "work time": "hours",
            "productivity": "hours",
            "trends": "trends", "מגמות": "trends", "מגמה": "trends",
            "progress": "trends", "התקדמות": "trends",
            "השתפרתי": "trends", "improving": "trends",
            "streak": "streak", "רצף": "streak", "רציפות": "streak",
            "consecutive": "streak",
            "scan": "scan", "סריקה": "scan", "בריאות": "scan",
            "health": "scan",
            "בדיקה": "scan", "check": "scan",
            "vs": "vs", "השוואה": "vs", "compare": "vs", "להשוות": "vs",
            "versus": "vs", "לעומת": "vs", "difference": "vs",
            "log": "log", "לוג": "log", "history": "log",
            "היסטוריה": "log", "commits": "log",
            "help": "help", "עזרה": "help", "איך": "help",
            "how": "help", "commands": "help", "פקודות": "help",
            "multi": "multi", "מולטי": "multi", "ריפו": "multi",
            "all repos": "multi", "כל הריפו": "multi",
            "init": "init", "config": "init", "הגדרות": "init",
            "setup": "init",
            "diff": "diff", "שינויים": "diff", "changes": "diff",
            "מה השתנה": "diff", "what changed": "diff",
            "blame": "blame", "בעלות": "blame", "ownership": "blame",
            "מי כתב": "blame", "who wrote": "blame", "who owns": "blame",
            "bus factor": "blame", "אחראי": "blame",
            "standup": "standup", "סטנדאפ": "standup",
            "morning": "standup", "בוקר": "standup",
            "what did i do": "standup", "מה עשיתי אתמול": "standup",
            "id": "id", "זהות": "id", "identity": "id", "card": "id",
            "כרטיס": "id", "about": "id",
            "quality": "quality", "איכות הודעות": "quality",
            "message quality": "quality", "commit quality": "quality",
            "age": "age", "גיל": "age", "stale": "age", "old": "age",
            "ישן": "age", "מת": "age",
        }

        # === Intents ===
        SMART_INTENTS = {
            "דוח": None, "report": None, "סיכום": None,
            "summary": None, "מה עשיתי": None, "what did i do": None,
            "מה קורה": None, "status": None, "סטטוס": None,
            "מה נעשה": None, "what happened": None,
            "מה חדש": None, "what's new": None,
            "תראה לי": None, "show me": None, "הראה": None,
            "אני רוצה לראות": None, "i want to see": None,
            "תפתח": None, "open": None, "run": None, "תריץ": None,
        }

        # Time
        SMART_TIME = {
            "today": "--today", "היום": "--today", "יומי": "--today",
            "daily": "--today", "של היום": "--today",
            "week": "--week", "שבוע": "--week", "שבועי": "--week",
            "weekly": "--week", "השבוע": "--week", "this week": "--week",
            "month": "--month", "חודש": "--month", "חודשי": "--month",
            "monthly": "--month", "החודש": "--month", "this month": "--month",
        }

        # Flags
        SMART_FLAGS = {
            "beginner": "--beginner", "מתחיל": "--beginner",
            "מתחילים": "--beginner", "הסברים": "--beginner",
            "explain": "--beginner", "simple": "--beginner",
            "פשוט": "--beginner",
            "json": "--json",
            "hebrew": "--lang he", "עברית": "--lang he",
        }

        detected_command = None
        detected_time = None
        detected_flags = []
        has_intent = False

        for keyword, cmd in SMART_KEYWORDS.items():
            if keyword in all_words:
                detected_command = cmd
                break

        if not detected_command:
            for intent_word in SMART_INTENTS:
                if intent_word in all_words:
                    has_intent = True
                    break

        for keyword, flag in SMART_TIME.items():
            if keyword in all_words:
                detected_time = flag
                break

        for keyword, flag in SMART_FLAGS.items():
            if keyword in all_words:
                detected_flags.append(flag)

        # === Build command ===
        if detected_command:
            new_argv = [detected_command]
            if detected_flags:
                for f in detected_flags:
                    new_argv.extend(f.split())
            if detected_time and detected_command in (
                "team", "hours", "vs", "trends"
            ):
                time_to_days = {
                    "--today": "1", "--week": "7", "--month": "30",
                }
                new_argv.append(time_to_days.get(detected_time, "7"))
            elif detected_time and detected_command not in (
                "learn", "scan", "help", "streak", "init",
                "team", "hours", "vs", "trends", "log",
            ):
                new_argv.append(detected_time)

            console.print(
                f"  [dim]→ understood: pulse {' '.join(new_argv)}[/dim]\n"
            )
            argv = new_argv
            first = argv[0]

        elif has_intent and detected_time:
            new_argv = [detected_time]
            if detected_flags:
                for f in detected_flags:
                    new_argv.extend(f.split())
            console.print(
                f"  [dim]→ understood: pulse {' '.join(new_argv)}[/dim]\n"
            )
            argv = new_argv
            first = argv[0]

        elif has_intent and not detected_time:
            new_argv = []
            if detected_flags:
                for f in detected_flags:
                    new_argv.extend(f.split())
            console.print(
                f"  [dim]→ understood: pulse {' '.join(new_argv) if new_argv else '(weekly report)'}[/dim]\n"
            )
            argv = new_argv if new_argv else []
            first = argv[0] if argv else ""

        else:
            console.print(
                f"  [yellow]I didn't understand '{' '.join(argv)}'.[/yellow]\n"
                f"  Did you mean one of these?\n"
                f"    [cyan]pulse today[/cyan]     — daily report\n"
                f"    [cyan]pulse scan[/cyan]      — project health\n"
                f"    [cyan]pulse team[/cyan]      — contributors\n"
                f"    [cyan]pulse hours[/cyan]     — work patterns\n"
                f"    [cyan]pulse learn[/cyan]     — code guide\n"
                f"    [cyan]pulse help[/cyan]      — all commands\n"
            )
            return None

    # Special commands — each runs a dedicated function
    if first == "scan":
        repo = argv[1] if len(argv) > 1 else "."
        scan_code(repo)
        return None

    if first == "team":
        repo = argv[1] if len(argv) > 1 else "."
        days = 30
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

    if first == "diff":
        count = 5
        repo = "."
        if len(argv) > 1 and argv[1].isdigit():
            count = int(argv[1])
            repo = argv[2] if len(argv) > 2 else "."
        elif len(argv) > 1:
            repo = argv[1]
        diff_report(repo, count)
        return None

    if first == "blame":
        repo = argv[1] if len(argv) > 1 else "."
        blame_report(repo)
        return None

    if first == "standup":
        repo = argv[1] if len(argv) > 1 else "."
        standup_report(repo)
        return None

    if first == "id":
        repo = argv[1] if len(argv) > 1 else "."
        id_report(repo)
        return None

    if first == "quality":
        repo = argv[1] if len(argv) > 1 else "."
        count = 100
        if len(argv) > 1 and argv[1].isdigit():
            count = int(argv[1])
            repo = argv[2] if len(argv) > 2 else "."
        commit_quality_report(repo, count)
        return None

    if first == "age":
        repo = argv[1] if len(argv) > 1 else "."
        code_age_report(repo)
        return None

    if first == "changelog":
        repo = "."
        output = None
        for arg in argv[1:]:
            if arg.endswith(".md"):
                output = arg
            else:
                repo = arg
        changelog_report(repo, output)
        return None

    if first == "hook":
        repo = argv[1] if len(argv) > 1 else "."
        install_hook(repo)
        return None

    if first == "watch":
        repo = argv[1] if len(argv) > 1 else "."
        watch_dashboard(repo)
        return None

    if first == "learn":
        beginner = "--beginner" in argv or "-b" in argv
        rest = [a for a in argv[1:] if a not in ("--beginner", "-b")]
        repo = rest[0] if rest else "."
        output = rest[1] if len(rest) > 1 else "learn.html"
        learn_report(repo, output, beginner=beginner)
        return None

    if first == "trends":
        repo = "."
        weeks = 8
        if len(argv) > 1 and argv[1].isdigit():
            weeks = int(argv[1])
            repo = argv[2] if len(argv) > 2 else "."
        elif len(argv) > 1:
            repo = argv[1]
        trends_report(repo, weeks)
        return None

    if first == "help":
        show_help()
        return None

    # since/s = needs the date after it
    if first in ("since", "s") and len(argv) > 1:
        return ["--since", argv[1]] + argv[2:]

    # Regular shortcut
    if first in SHORTCUTS and SHORTCUTS[first] is not None:
        return SHORTCUTS[first] + argv[1:]

    return argv


def interactive_mode():
    """Interactive mode — menu-based option selection."""
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]ContextPulse[/bold cyan] - Interactive Mode",
            border_style="cyan",
        )
    )
    console.print()

    # Step 1: Choose repo
    repo_path = Prompt.ask(
        "Repository path",
        default=".",
    )

    try:
        Repo(repo_path)
    except (InvalidGitRepositoryError, NoSuchPathError):
        console.print(f"[red]Error:[/red] '{repo_path}' is not a Git repository.")
        return

    # Step 2: Choose time range
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

    # Step 3: Filter by author?
    console.print()
    author = Prompt.ask("Filter by author (leave empty for all)", default="")
    author_filter = author if author else None
    if author_filter:
        period_label += f" (author: {author_filter})"

    # Step 4: Run
    console.print()
    commits = get_commits(repo_path, days, author_filter)
    display_report(commits, period_label)

    # Step 5: Export?
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
