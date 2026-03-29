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

import argparse
import sys
from datetime import datetime

from git.exc import InvalidGitRepositoryError, NoSuchPathError
from rich.panel import Panel

from .config import THEMES, current_lang, current_theme
from . import config
from .ui import console, show_logo
from .git_utils import get_commits, get_compare_commits
from .reports import display_report
from .export import export_json, export_markdown, export_html
from .smart import expand_shortcuts, interactive_mode


def main():
    """Main entry point."""

    # === Expand shortcuts ===
    expanded = expand_shortcuts(sys.argv[1:])
    if expanded is None:
        return  # command already ran

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

    # === Time shortcuts ===
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
        version="ContextPulse 1.2.0",
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

    # === Set language and theme ===
    config.current_lang = args.lang
    config.current_theme = THEMES.get(args.theme, THEMES["default"])

    # === Interactive mode ===
    if args.interactive:
        interactive_mode()
        return

    # === Calculate days ===
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

    # === Error handling ===
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

    # === Display ===
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
