"""
ContextPulse - Console setup, logo, and help display.
"""

from rich.console import Console
from rich.table import Table

from .config import th

console = Console()

LOGO = """[bold cyan]
   ____            _            _   ____        _
  / ___|___  _ __ | |_ _____  _| |_|  _ \\ _   _| |___  ___
 | |   / _ \\| '_ \\| __/ _ \\ \\/ / __| |_) | | | | / __|/ _ \\
 | |__| (_) | | | | ||  __/>  <| |_|  __/| |_| | \\__ \\  __/
  \\____\\___/|_| |_|\\__\\___/_/\\_\\\\__|_|    \\__,_|_|___/\\___|
[/bold cyan][dim]  Turn your Git history into a human story[/dim]
"""


def show_logo():
    """Displays the ContextPulse logo."""
    console.print(LOGO)


def show_help():
    """
    pulse help: Pretty guide with all commands.
    """
    show_logo()

    # Main commands
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
    cmds.add_row("pulse trends", "Weekly trends over time")
    cmds.add_row("pulse diff", "Show exactly what changed recently")
    cmds.add_row("pulse blame", "Who owns what + Bus Factor")
    cmds.add_row("pulse standup", "Auto standup report (paste to Slack)")
    cmds.add_row("pulse id", "Repo identity card")
    cmds.add_row("pulse quality", "Commit message quality score")
    cmds.add_row("pulse age", "Code age map (stale file detection)")
    cmds.add_row("pulse learn", "Generate code guide (HTML)")
    cmds.add_row("pulse learn --beginner", "Code guide with explanations")
    cmds.add_row("pulse badges", "Your achievements")
    cmds.add_row("pulse leaderboard", "Contributor ranking")
    cmds.add_row("pulse changelog", "Auto-generate changelog")
    cmds.add_row("pulse log", "Pretty git log with icons")
    cmds.add_row("pulse multi PATH", "Scan all repos in a directory")
    cmds.add_row("pulse hook", "Install post-commit mini report")
    cmds.add_row("pulse watch", "Live dashboard (auto-refresh)")
    cmds.add_row("pulse init", "Create .pulserc config file")
    cmds.add_row("pulse i", "Interactive mode (guided menu)")
    cmds.add_row("pulse help", "This help page")
    console.print(cmds)

    # Options
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

    # Examples
    console.print()
    console.print("[bold]Examples:[/bold]")
    console.print("  [dim]$[/dim] pulse month --lang he")
    console.print("  [dim]$[/dim] pulse --theme ocean --export report.md")
    console.print("  [dim]$[/dim] pulse team 90 ~/code/my-project")
    console.print("  [dim]$[/dim] pulse multi ~/code")
    console.print("  [dim]$[/dim] pulse vs 14")
    console.print()
