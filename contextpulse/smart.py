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
    watch_dashboard, badges_report, leaderboard_report,
)
from .ui import console, show_help
from rich.panel import Panel


def _parse_args(argv, has_days=False, default_days=30):
    """
    Helper: מנתח ארגומנטים לפקודות מיוחדות.
    מחזיר (repo, days) או (repo,) לפי has_days.
    """
    repo = "."
    days = default_days

    if has_days:
        if len(argv) > 1 and argv[1].isdigit():
            days = int(argv[1])
            repo = argv[2] if len(argv) > 2 else "."
        elif len(argv) > 1:
            repo = argv[1]
        return repo, days
    else:
        if len(argv) > 1:
            repo = argv[1]
        return (repo,)


def _safe_run(func, *args, **kwargs):
    """
    Helper: מריץ פונקציה עם error handling לנתיבים לא תקינים.
    במקום קריסה — הודעת שגיאה יפה.
    """
    try:
        func(*args, **kwargs)
    except InvalidGitRepositoryError:
        repo = args[0] if args else "."
        console.print(
            Panel(
                f"[red]'{repo}' is not a Git repository.[/red]\n\n"
                "Make sure you're inside a Git project, or specify a path:\n"
                "  [cyan]pulse <command> ~/code/my-project[/cyan]",
                title="Not a Git Repository",
                border_style="red",
            )
        )
    except NoSuchPathError:
        repo = args[0] if args else "."
        console.print(
            Panel(
                f"[red]Path '{repo}' does not exist.[/red]",
                title="Path Not Found",
                border_style="red",
            )
        )
    except ValueError as e:
        if "does not exist" in str(e).lower() or "reference" in str(e).lower():
            console.print("[yellow]This repository has no commits yet.[/yellow]")
        else:
            console.print(f"[red]Error:[/red] {e}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


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
    "badges": None,
    "leaderboard": None,
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
    "הישגים": None,      # = badges
    "דירוג": None,       # = leaderboard
    "עזרה": None,
}


# === Hebrew → English translation map ===
HEBREW_COMMANDS = {
    "צוות": "team", "שעות": "hours", "לימוד": "learn",
    "מגמות": "trends", "רצף": "streak", "סריקה": "scan",
    "השוואה": "vs", "לוג": "log", "שינויים": "diff",
    "בעלות": "blame", "סטנדאפ": "standup", "זהות": "id",
    "איכות": "quality", "גיל": "age",
    "שינויון": "changelog", "הוק": "hook", "צפייה": "watch",
    "הישגים": "badges", "דירוג": "leaderboard",
    "עזרה": "help",
}

# === Smart NLP keyword maps ===
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
    "health": "scan", "בדיקה": "scan", "check": "scan",
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
    "age": "age", "גיל": "age", "stale": "age",
    "ישן": "age", "מת": "age",
    "changelog": "changelog",
    "watch": "watch", "צפייה": "watch", "live": "watch",
    "hook": "hook",
    "badges": "badges", "הישגים": "badges", "achievements": "badges",
    "leaderboard": "leaderboard", "דירוג": "leaderboard", "ranking": "leaderboard",
    "top": "leaderboard",
}

SMART_INTENTS = {
    "דוח", "report", "סיכום", "summary", "מה עשיתי",
    "what did i do", "מה קורה", "status", "סטטוס",
    "מה נעשה", "what happened", "מה חדש", "what's new",
    "תראה לי", "show me", "הראה", "אני רוצה לראות",
    "i want to see", "תפתח", "open", "run", "תריץ",
}

SMART_TIME = {
    "today": "--today", "היום": "--today", "יומי": "--today",
    "daily": "--today", "של היום": "--today",
    "week": "--week", "שבוע": "--week", "שבועי": "--week",
    "weekly": "--week", "השבוע": "--week", "this week": "--week",
    "month": "--month", "חודש": "--month", "חודשי": "--month",
    "monthly": "--month", "החודש": "--month", "this month": "--month",
}

SMART_FLAGS = {
    "beginner": "--beginner", "מתחיל": "--beginner",
    "מתחילים": "--beginner", "הסברים": "--beginner",
    "explain": "--beginner", "simple": "--beginner",
    "פשוט": "--beginner",
    "json": "--json",
    "hebrew": "--lang he", "עברית": "--lang he",
}


def _translate_hebrew(first, argv):
    """Step 1: Translate Hebrew command word to English."""
    if first in HEBREW_COMMANDS:
        first = HEBREW_COMMANDS[first]
        argv[0] = first
    return first, argv


def _parse_natural_language(argv):
    """
    Step 2: Parse free-form Hebrew/English input into a command.
    Returns (new_argv, new_first) or (None, None) if not understood.
    """
    all_words = " ".join(argv).lower()
    all_word_list = all_words.split()

    def _matches(keyword):
        if " " in keyword:
            return keyword in all_words
        return keyword in all_word_list

    detected_command = None
    detected_time = None
    detected_flags = []
    has_intent = False

    for keyword, cmd in SMART_KEYWORDS.items():
        if _matches(keyword):
            detected_command = cmd
            break

    if not detected_command:
        for intent_word in SMART_INTENTS:
            if _matches(intent_word):
                has_intent = True
                break

    for keyword, flag in SMART_TIME.items():
        if _matches(keyword):
            detected_time = flag
            break

    for keyword, flag in SMART_FLAGS.items():
        if _matches(keyword):
            detected_flags.append(flag)

    # Build command
    if detected_command:
        new_argv = [detected_command]
        if detected_flags:
            for f in detected_flags:
                new_argv.extend(f.split())
        if detected_time and detected_command in ("team", "hours", "vs", "trends"):
            time_to_days = {"--today": "1", "--week": "7", "--month": "30"}
            new_argv.append(time_to_days.get(detected_time, "7"))
        elif detected_time and detected_command not in (
            "learn", "scan", "help", "streak", "init",
            "team", "hours", "vs", "trends", "log",
        ):
            new_argv.append(detected_time)
        console.print(f"  [dim]→ understood: pulse {' '.join(new_argv)}[/dim]\n")
        return new_argv

    if has_intent and detected_time:
        new_argv = [detected_time]
        for f in detected_flags:
            new_argv.extend(f.split())
        console.print(f"  [dim]→ understood: pulse {' '.join(new_argv)}[/dim]\n")
        return new_argv

    if has_intent:
        new_argv = []
        for f in detected_flags:
            new_argv.extend(f.split())
        label = ' '.join(new_argv) if new_argv else '(weekly report)'
        console.print(f"  [dim]→ understood: pulse {label}[/dim]\n")
        return new_argv if new_argv else []

    # Not understood
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


# === Command dispatch table ===
# Maps command name → (function, has_days, default_days)
# has_days=None means special handling
COMMAND_TABLE = {
    "scan":      (scan_code, None, None),
    "team":      (team_report, True, 30),
    "hours":     (hours_report, True, 30),
    "vs":        (vs_report, True, 7),
    "multi":     (multi_report, True, 7),
    "streak":    (streak_report, None, None),
    "log":       (pretty_log, True, 20),
    "diff":      (diff_report, True, 5),
    "blame":     (blame_report, None, None),
    "standup":   (standup_report, None, None),
    "id":        (id_report, None, None),
    "quality":   (commit_quality_report, True, 100),
    "age":       (code_age_report, None, None),
    "hook":      (install_hook, None, None),
    "watch":     (watch_dashboard, None, None),
    "trends":    (trends_report, True, 8),
    "badges":    (badges_report, None, None),
    "leaderboard": (leaderboard_report, True, 30),
}


def _dispatch_command(first, argv):
    """
    Step 3: Dispatch a recognized command to its function.
    Returns True if handled, False if not a special command.
    """
    # Commands without error wrapping
    if first == "help":
        show_help()
        return True

    if first == "init":
        repo, = _parse_args(argv)
        init_config(repo)
        return True

    # Changelog has special arg parsing
    if first == "changelog":
        repo = "."
        output = None
        for arg in argv[1:]:
            if arg.endswith(".md"):
                output = arg
            else:
                repo = arg
        _safe_run(changelog_report, repo, output)
        return True

    # Learn has special flags
    if first == "learn":
        beginner = "--beginner" in argv or "-b" in argv
        rest = [a for a in argv[1:] if a not in ("--beginner", "-b")]
        repo = rest[0] if rest else "."
        output = rest[1] if len(rest) > 1 else "learn.html"
        _safe_run(learn_report, repo, output, beginner=beginner)
        return True

    # Table-driven dispatch
    if first in COMMAND_TABLE:
        func, has_days, default_days = COMMAND_TABLE[first]
        if has_days:
            repo, days = _parse_args(argv, has_days=True, default_days=default_days)
            _safe_run(func, repo, days)
        else:
            repo, = _parse_args(argv)
            _safe_run(func, repo)
        return True

    return False


def expand_shortcuts(argv):
    """
    Main entry point: translates user input into a command.
    3 steps: Hebrew translation → NLP parsing → command dispatch.
    """
    if not argv:
        return argv

    first = argv[0]

    # Step 1: Hebrew → English
    first, argv = _translate_hebrew(first, argv)

    # Step 2: Smart NLP mode (if not a known command)
    all_commands = set(SHORTCUTS.keys()) | set(HEBREW_COMMANDS.keys())
    if first not in all_commands and not first.startswith("-") and not first.startswith("/"):
        result = _parse_natural_language(argv)
        if result is None:
            return None
        argv = result
        first = argv[0] if argv else ""

    # Step 3: Dispatch special commands
    if _dispatch_command(first, argv):
        return None

    # Simple shortcuts (today → --today, etc.)
    if first in ("since", "s") and len(argv) > 1:
        return ["--since", argv[1]] + argv[2:]

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
