"""
ContextPulse - All report display functions.
"""

import datetime as _dt_module
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from git import Repo
from rich.panel import Panel
from rich.table import Table

from .config import CATEGORY_COLORS, get_category, t, th
from .ui import console, show_logo


def group_by_category(commits):
    """Groups all changes by category."""
    categories = defaultdict(lambda: {"commits": 0, "files": set()})

    for commit in commits:
        for filename in commit["files"]:
            cat = get_category(filename)
            categories[cat]["commits"] += 1
            categories[cat]["files"].add(filename)

    return categories


def group_by_directory(commits):
    """Groups changes by directory (useful for monorepo)."""
    dirs = defaultdict(lambda: {"commits": 0, "files": set()})

    for commit in commits:
        for filename in commit["files"]:
            parts = Path(filename).parts
            if len(parts) > 1:
                top_dir = parts[0]
            else:
                top_dir = "(root)"
            dirs[top_dir]["commits"] += 1
            dirs[top_dir]["files"].add(filename)

    return dirs


def get_hot_files(commits, top_n=5):
    """Finds the most frequently changed files ("hot spots")."""
    file_counts = Counter()
    for commit in commits:
        for filename in commit["files"]:
            file_counts[filename] += 1

    return file_counts.most_common(top_n)


def generate_summary(commits, categories):
    """Creates a human-readable text summary."""
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
        activities.append(t("bug_fixes"))
    if "add" in messages:
        activities.append(t("new_features"))
    if "update" in messages or "improve" in messages:
        activities.append(t("improvements"))
    if "refactor" in messages:
        activities.append(t("refactoring"))
    if "test" in messages:
        activities.append(t("testing"))
    if "doc" in messages or "readme" in messages:
        activities.append(t("documentation"))
    if not activities:
        activities.append(t("various"))

    activity_str = ", ".join(activities)
    commit_word = "commit" if total_commits == 1 else t("commits_word")
    summary = (
        f"{t('you_made')} {total_commits} {commit_word}, "
        f"{t('focusing_on')} {top_cat} ({top_pct}%). "
        f"{t('main_activities')}: {activity_str}."
    )

    if len(sorted_cats) > 1:
        others = [c[0] for c in sorted_cats[1:3]]
        summary += f" {t('also_touched')}: {', '.join(others)}."

    return summary


def display_activity_chart(commits):
    """Activity chart — shows which days were most active."""
    if not commits:
        return

    day_counts = Counter(c["date_short"] for c in commits)
    sorted_days = sorted(day_counts.items())

    console.print()
    console.print(f"[bold]{t('daily_activity')}[/bold]")

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
    """Displays top 5 most changed files."""
    hot = get_hot_files(commits)
    if not hot:
        return

    console.print()
    hot_table = Table(
        title=t("hot_files"),
        show_header=True,
        header_style="bold red",
    )
    hot_table.add_column("#", style="dim", width=3)
    hot_table.add_column("File", style="white")
    hot_table.add_column("Changes", justify="right", style="red")

    for i, (filename, count) in enumerate(hot, 1):
        fire = "🔥 " if count >= 5 else "   "
        hot_table.add_row(str(i), f"{fire}{filename}", str(count))

    console.print(hot_table)


def display_directory_breakdown(commits):
    """Shows breakdown by directory (useful for monorepo)."""
    dirs = group_by_directory(commits)
    if len(dirs) <= 1:
        return

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
    for dir_name, data in sorted_dirs[:10]:
        dir_table.add_row(
            dir_name,
            str(data["commits"]),
            str(len(data["files"])),
        )

    console.print(dir_table)


def display_report(commits, period_label):
    """Displays the full report in terminal."""
    if not commits:
        console.print(
            Panel(t("no_commits"), style="yellow")
        )
        return

    # === Title ===
    console.print()
    console.print(
        Panel.fit(
            f"[{th('title')}]ContextPulse[/{th('title')}] - {t('report_title')}\n"
            f"[{th('subtitle')}]{period_label}[/{th('subtitle')}]",
            subtitle=f"{len(commits)} {t('commits_word')}",
            border_style=th("border"),
        )
    )

    # === Text summary ===
    categories = group_by_category(commits)
    summary = generate_summary(commits, categories)
    console.print()
    console.print(Panel(summary, title=t("summary"), border_style=th("summary_border")))

    # === Commits table ===
    console.print()
    table = Table(
        title=t("commits"),
        show_header=True,
        header_style=th("header"),
    )
    table.add_column(t("date"), style="dim", width=16)
    table.add_column(t("hash"), style=th("accent"), width=9)
    table.add_column(t("message"), style="white")
    table.add_column(t("files"), justify="right", style=th("positive"))

    for commit in commits:
        table.add_row(
            commit["date"],
            commit["hash"],
            commit["message"],
            str(commit["files_changed"]),
        )

    console.print(table)

    # === Categories table ===
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

    # === Directory breakdown ===
    display_directory_breakdown(commits)

    # === Daily activity chart ===
    display_activity_chart(commits)

    # === Diff Summary ===
    total_insertions = sum(c.get("insertions", 0) for c in commits)
    total_deletions = sum(c.get("deletions", 0) for c in commits)
    if total_insertions > 0 or total_deletions > 0:
        console.print()
        console.print(
            f"  [{th('positive')}]+{total_insertions} {t('lines_added')}[/{th('positive')}]  "
            f"[{th('negative')}]-{total_deletions} {t('lines_removed')}[/{th('negative')}]  "
            f"[{th('neutral')}]({t('net')}: {total_insertions - total_deletions:+d})[/{th('neutral')}]"
        )

    # === Summary line ===
    total_files = sum(c["files_changed"] for c in commits)
    authors = set(c["author"] for c in commits)
    console.print()
    console.print(
        f"  [bold]{t('total')}:[/bold] {len(commits)} {t('commits_word')} "
        f"{t('by')} {len(authors)} {t('author_s')}, "
        f"{total_files} {t('file_changes')}"
    )
    console.print()


def team_report(repo_path=".", days=30):
    """pulse team: Shows who is most active in the project."""
    repo = Repo(repo_path)
    since_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

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
        console.print(Panel(t("no_commits"), style="yellow"))
        return

    show_logo()
    total_commits = sum(a["commits"] for a in authors.values())

    console.print(
        Panel.fit(
            f"[{th('title')}]{t('team_report')}[/{th('title')}] — last {days} days",
            subtitle=f"{len(authors)} contributor(s)",
        )
    )
    console.print()

    table = Table(
        title=t("contributors"),
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
        bar = "█" * (pct // 5)
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
    """pulse hours: Analyzes which hours and days you are most active."""
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
        console.print(Panel(t("no_commits"), style="yellow"))
        return

    show_logo()
    console.print(
        Panel.fit(
            f"[{th('title')}]{t('work_patterns')}[/{th('title')}] — last {days} days",
        )
    )

    # === Hours ===
    console.print()
    console.print(f"[bold]{t('activity_by_hour')}[/bold]")

    max_hour = max(hour_counts.values()) if hour_counts else 1

    for hour in range(24):
        count = hour_counts.get(hour, 0)
        bar_len = round(count / max_hour * 25) if count > 0 else 0
        bar = "█" * bar_len

        if 6 <= hour < 12:
            color = "yellow"
        elif 12 <= hour < 18:
            color = "green"
        elif 18 <= hour < 22:
            color = "red"
        else:
            color = "blue"

        hour_str = f"{hour:02d}:00"
        if count > 0:
            console.print(
                f"  {hour_str}  [{color}]{bar}[/{color}] {count}"
            )
        else:
            console.print(f"  {hour_str}  [dim]·[/dim]")

    # === Days ===
    console.print()
    console.print(f"[bold]{t('activity_by_day')}[/bold]")

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

    # === Insights ===
    console.print()
    if hour_counts:
        peak_hour = max(hour_counts, key=hour_counts.get)
        console.print(
            f"  [bold]{t('peak_hour')}:[/bold] {peak_hour:02d}:00 "
            f"({hour_counts[peak_hour]} {t('commits_word')})"
        )
    if day_counts:
        peak_day = max(day_counts, key=day_counts.get)
        console.print(
            f"  [bold]{t('peak_day')}:[/bold] {peak_day} "
            f"({day_counts[peak_day]} {t('commits_word')})"
        )

    # Pattern detection
    morning = sum(hour_counts.get(h, 0) for h in range(6, 12))
    afternoon = sum(hour_counts.get(h, 0) for h in range(12, 18))
    evening = sum(hour_counts.get(h, 0) for h in range(18, 22))
    night = sum(hour_counts.get(h, 0) for h in range(22, 24))
    night += sum(hour_counts.get(h, 0) for h in range(0, 6))

    periods = {
        t("morning_person"): morning,
        t("afternoon_coder"): afternoon,
        t("evening_hacker"): evening,
        t("night_owl"): night,
    }
    top_period = max(periods, key=periods.get)
    console.print(f"  [bold]{t('pattern')}:[/bold] {t('youre_a')} {top_period}")
    console.print()


def vs_report(repo_path=".", days=7):
    """pulse vs: Compares current period to previous period."""
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
            f"[{th('title')}]{t('period_comparison')}[/{th('title')}]\n"
            f"[dim]Current {days} days vs previous {days} days[/dim]",
        )
    )
    console.print()

    # === Comparison table ===
    table = Table(
        show_header=True,
        header_style="bold blue",
    )
    table.add_column("Metric", style="bold")
    table.add_column(f"Previous {days}d", justify="right")
    table.add_column(f"Current {days}d", justify="right")
    table.add_column("Change", justify="right")

    def change_str(current, previous):
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

    # === Summary ===
    console.print()
    if curr_count > prev_count:
        console.print(
            f"  [{th('positive')}]↑ {t('productivity_up')}[/{th('positive')}] "
            f"{curr_count} vs {prev_count} {t('commits_word')}"
        )
    elif curr_count < prev_count:
        console.print(
            f"  [{th('negative')}]↓ {t('slower_period')}[/{th('negative')}] "
            f"{curr_count} vs {prev_count} {t('commits_word')}"
        )
    else:
        console.print(f"  [dim]{t('same_pace')}[/dim]")
    console.print()


def _calc_streak(commit_days):
    """Helper: מחשב רצף נוכחי מתוך סט של ימים עם קומיטים."""
    today = datetime.now().strftime("%Y-%m-%d")
    current_streak = 0
    check_date = datetime.now()

    while True:
        day_str = check_date.strftime("%Y-%m-%d")
        if day_str in commit_days:
            current_streak += 1
            check_date = check_date.replace(
                hour=0, minute=0, second=0
            ) - _dt_module.timedelta(days=1)
        else:
            if current_streak == 0 and day_str == today:
                check_date = check_date.replace(
                    hour=0, minute=0, second=0
                ) - _dt_module.timedelta(days=1)
                continue
            break
    return current_streak


def _get_commit_days(repo):
    """Helper: מחזיר סט של ימים שהיו בהם קומיטים.
    Uses git log --format directly — much faster than iterating commit objects."""
    try:
        output = repo.git.log("--format=%cd", "--date=short")
        return set(output.strip().split("\n")) if output.strip() else set()
    except Exception:
        return set()


def streak_report(repo_path="."):
    """pulse streak: Shows how many consecutive days you commit."""
    repo = Repo(repo_path)

    commit_days = _get_commit_days(repo)

    if not commit_days:
        console.print(Panel(t("no_commits"), style="yellow"))
        return

    current_streak = _calc_streak(commit_days)

    # Find best streak ever
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

    # Display
    show_logo()
    console.print()

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

    # Calendar for last 28 days
    console.print()
    console.print("[bold]Last 28 days:[/bold]")
    line = "  "
    for i in range(27, -1, -1):
        day = datetime.now() - _dt_module.timedelta(days=i)
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
    """pulse log: Pretty git log with colors, categories, and summary."""
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


def trends_report(repo_path=".", weeks=8):
    """pulse trends: Shows trends over time — commits per week."""
    repo = Repo(repo_path)
    days = weeks * 7
    since_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

    week_counts = Counter()
    week_files = Counter()
    week_insertions = Counter()

    for commit in repo.iter_commits():
        if commit.committed_date < since_date:
            break
        commit_dt = datetime.fromtimestamp(commit.committed_date)
        year, week_num, _ = commit_dt.isocalendar()
        key = f"{year}-W{week_num:02d}"
        week_counts[key] += 1
        week_files[key] += len(commit.stats.files)
        week_insertions[key] += commit.stats.total.get("insertions", 0)

    if not week_counts:
        console.print(Panel(t("no_commits"), style="yellow"))
        return

    show_logo()
    console.print(
        Panel.fit(
            f"[{th('title')}]Trends[/{th('title')}] — last {weeks} weeks",
            border_style=th("border"),
        )
    )

    sorted_weeks = sorted(week_counts.keys())
    max_count = max(week_counts.values())

    console.print()
    console.print("[bold]Commits per Week[/bold]")

    prev_count = None
    for week_key in sorted_weeks:
        count = week_counts[week_key]
        bar_len = round(count / max_count * 30)
        bar = "█" * bar_len

        if prev_count is not None:
            if count > prev_count:
                trend = f"[green]↑ +{count - prev_count}[/green]"
            elif count < prev_count:
                trend = f"[red]↓ {count - prev_count}[/red]"
            else:
                trend = "[dim]=[/dim]"
        else:
            trend = ""

        color = th("positive") if count >= max_count * 0.7 else (
            th("accent") if count >= max_count * 0.4 else th("neutral")
        )
        console.print(
            f"  {week_key}  [{color}]{bar}[/{color}] {count}  {trend}"
        )
        prev_count = count

    # Statistics
    counts = list(week_counts.values())
    avg = round(sum(counts) / len(counts), 1)
    best_week = max(week_counts, key=week_counts.get)
    worst_week = min(week_counts, key=week_counts.get)

    console.print()
    console.print(f"  [bold]Average:[/bold] {avg} commits/week")
    console.print(
        f"  [bold]Best week:[/bold] {best_week} "
        f"({week_counts[best_week]} commits)"
    )
    console.print(
        f"  [bold]Slowest:[/bold] {worst_week} "
        f"({week_counts[worst_week]} commits)"
    )

    # Overall trend
    half = len(counts) // 2
    if half > 0:
        first_half_avg = sum(counts[:half]) / half
        second_half_avg = sum(counts[half:]) / len(counts[half:])
        if second_half_avg > first_half_avg * 1.1:
            console.print(
                f"\n  [{th('positive')}]Trend: Accelerating! "
                f"You're getting more productive.[/{th('positive')}]"
            )
        elif second_half_avg < first_half_avg * 0.9:
            console.print(
                f"\n  [{th('negative')}]Trend: Slowing down. "
                f"Recent weeks are less active.[/{th('negative')}]"
            )
        else:
            console.print(
                f"\n  [{th('accent')}]Trend: Steady pace. "
                f"Consistent work![/{th('accent')}]"
            )

    console.print()


def diff_report(repo_path=".", count=5):
    """pulse diff: Shows exactly what changed in recent commits."""
    repo = Repo(repo_path)

    show_logo()
    console.print(
        Panel.fit(
            f"[{th('title')}]Recent Changes[/{th('title')}]",
            subtitle=f"last {count} commits",
            border_style=th("border"),
        )
    )

    for i, commit in enumerate(repo.iter_commits(max_count=count)):
        commit_dt = datetime.fromtimestamp(commit.committed_date)
        date_str = commit_dt.strftime("%Y-%m-%d %H:%M")
        msg = commit.message.strip().split("\n")[0]
        hash_short = commit.hexsha[:7]
        stats = commit.stats

        console.print()
        console.print(
            f"  [{th('accent')}]{hash_short}[/{th('accent')}] "
            f"[dim]{date_str}[/dim] — {msg}"
        )

        for filepath, file_stats in stats.files.items():
            ins = file_stats.get("insertions", 0)
            dels = file_stats.get("deletions", 0)

            total = ins + dels
            if total > 0:
                bar_len = min(total, 40)
                ins_len = round(ins / total * bar_len)
                del_len = bar_len - ins_len
                bar = (
                    f"[green]{'+' * ins_len}[/green]"
                    f"[red]{'-' * del_len}[/red]"
                )
            else:
                bar = ""

            if dels == 0 and ins > 0:
                icon = "[green]+ new[/green]"
            elif ins == 0 and dels > 0:
                icon = "[red]- del[/red]"
            else:
                icon = "[yellow]~ mod[/yellow]"

            cat = get_category(filepath)
            color = CATEGORY_COLORS.get(cat, "white")

            console.print(
                f"    {icon} [{color}]{filepath}[/{color}]  "
                f"{bar}  "
                f"[green]+{ins}[/green] [red]-{dels}[/red]"
            )

        total_ins = stats.total.get("insertions", 0)
        total_dels = stats.total.get("deletions", 0)
        console.print(
            f"    [dim]── {len(stats.files)} files, "
            f"+{total_ins}/-{total_dels} lines[/dim]"
        )

        if i < count - 1:
            console.print("    [dim]│[/dim]")

    console.print()


def blame_report(repo_path=".", top_n=10):
    """pulse blame: Shows who owns what in the project + Bus Factor."""
    repo = Repo(repo_path)
    project_name = Path(repo_path).resolve().name

    show_logo()
    console.print(
        Panel.fit(
            f"[{th('title')}]Code Ownership — {project_name}[/{th('title')}]",
            border_style=th("border"),
        )
    )

    all_files = repo.git.ls_files().split("\n")
    all_files = [f for f in all_files if f]

    text_extensions = {
        ".py", ".js", ".ts", ".html", ".css", ".jsx", ".tsx",
        ".rb", ".go", ".rs", ".java", ".sh", ".sql", ".md",
        ".txt", ".json", ".yml", ".yaml", ".toml",
    }

    dir_owners = defaultdict(lambda: Counter())
    file_owners = defaultdict(lambda: Counter())
    bus_factor_files = []

    console.print()
    console.print("[dim]Analyzing ownership (this may take a moment)...[/dim]")

    files_analyzed = 0
    for filepath in all_files:
        suffix = Path(filepath).suffix.lower()
        if suffix not in text_extensions:
            continue

        try:
            blame_output = repo.git.blame("--line-porcelain", filepath)
        except Exception:
            continue

        files_analyzed += 1
        authors_in_file = Counter()

        for line in blame_output.split("\n"):
            if line.startswith("author "):
                author = line[7:]
                authors_in_file[author] += 1

                parts = Path(filepath).parts
                top_dir = parts[0] if len(parts) > 1 else "(root)"
                dir_owners[top_dir][author] += 1

        if authors_in_file:
            top_author = authors_in_file.most_common(1)[0]
            total_lines = sum(authors_in_file.values())
            ownership_pct = round(top_author[1] / total_lines * 100)
            file_owners[filepath] = {
                "author": top_author[0],
                "pct": ownership_pct,
                "lines": total_lines,
                "unique_authors": len(authors_in_file),
            }

            if len(authors_in_file) == 1:
                bus_factor_files.append(filepath)

    # === Directory ownership table ===
    console.print()
    dir_table = Table(
        title="Ownership by Directory",
        show_header=True,
        header_style=th("header"),
    )
    dir_table.add_column("Directory", style="bold")
    dir_table.add_column("Top Owner", style=th("accent"))
    dir_table.add_column("%", justify="right", style=th("positive"))
    dir_table.add_column("Authors", justify="right")

    for dir_name in sorted(dir_owners.keys()):
        authors = dir_owners[dir_name]
        total = sum(authors.values())
        top = authors.most_common(1)[0]
        pct = round(top[1] / total * 100)
        num_authors = len(authors)

        pct_color = th("positive") if pct < 80 else (
            "yellow" if pct < 95 else th("negative")
        )
        dir_table.add_row(
            dir_name,
            top[0],
            f"[{pct_color}]{pct}%[/{pct_color}]",
            str(num_authors),
        )

    console.print(dir_table)

    # === High ownership files ===
    single_owner = sorted(
        [
            (f, d) for f, d in file_owners.items()
            if d["pct"] >= 90 and d["lines"] >= 10
        ],
        key=lambda x: x[1]["lines"],
        reverse=True,
    )[:top_n]

    if single_owner:
        console.print()
        file_table = Table(
            title="High Ownership Files (90%+ by one person)",
            show_header=True,
            header_style="bold yellow",
        )
        file_table.add_column("File", style="white")
        file_table.add_column("Owner", style=th("accent"))
        file_table.add_column("%", justify="right")
        file_table.add_column("Lines", justify="right", style="dim")

        for filepath, data in single_owner:
            file_table.add_row(
                filepath,
                data["author"],
                f"{data['pct']}%",
                str(data["lines"]),
            )

        console.print(file_table)

    # === Bus Factor ===
    all_authors = set()
    for authors in dir_owners.values():
        all_authors.update(authors.keys())

    bus_factor = len(all_authors)

    console.print()
    if bus_factor <= 1:
        bf_color = th("negative")
        bf_msg = "CRITICAL — only 1 contributor knows the code"
    elif bus_factor <= 2:
        bf_color = "yellow"
        bf_msg = "LOW — consider getting more contributors"
    else:
        bf_color = th("positive")
        bf_msg = "Healthy — knowledge is distributed"

    console.print(
        Panel(
            f"[{bf_color}]Bus Factor: {bus_factor}[/{bf_color}]\n"
            f"[dim]{bf_msg}[/dim]\n\n"
            f"Files analyzed: {files_analyzed}\n"
            f"Single-author files: {len(bus_factor_files)}",
            title="Bus Factor",
            border_style=bf_color,
        )
    )
    console.print()


def standup_report(repo_path=".", author_filter=None):
    """
    pulse standup: יוצר דוח סטנדאפ קצר — מוכן להדבקה ב-Slack.
    מראה מה עשית אתמול (או היום) בפורמט נקי.
    """
    repo = Repo(repo_path)

    # מחפשים קומיטים מאתמול והיום
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0).timestamp()
    yesterday_start = today_start - (24 * 60 * 60)

    today_commits = []
    yesterday_commits = []

    for commit in repo.iter_commits():
        if commit.committed_date < yesterday_start:
            break

        if author_filter:
            if author_filter.lower() not in str(commit.author).lower():
                continue

        msg = commit.message.strip().split("\n")[0]
        files = list(commit.stats.files.keys())
        ins = commit.stats.total.get("insertions", 0)
        dels = commit.stats.total.get("deletions", 0)
        entry = {"message": msg, "files": len(files), "ins": ins, "dels": dels}

        if commit.committed_date >= today_start:
            today_commits.append(entry)
        else:
            yesterday_commits.append(entry)

    show_logo()

    # אתמול
    if yesterday_commits:
        console.print("[bold]Yesterday:[/bold]")
        total_files = 0
        total_ins = 0
        for c in yesterday_commits:
            console.print(f"  • {c['message']}")
            total_files += c["files"]
            total_ins += c["ins"]
        console.print(
            f"  [dim]{len(yesterday_commits)} tasks · "
            f"{total_files} files · +{total_ins} lines[/dim]"
        )
    else:
        console.print("[dim]Yesterday: no commits[/dim]")

    console.print()

    # היום
    if today_commits:
        console.print("[bold]Today so far:[/bold]")
        for c in today_commits:
            console.print(f"  • {c['message']}")
    else:
        console.print("[dim]Today: no commits yet[/dim]")

    # פלט מוכן להדבקה
    console.print()
    console.print("[bold yellow]Copy-paste for Slack:[/bold yellow]")
    console.print("[dim]─────────────────────[/dim]")

    if yesterday_commits:
        console.print("Yesterday I:")
        for c in yesterday_commits:
            console.print(f"• {c['message']}")

    if today_commits:
        console.print("Today:")
        for c in today_commits:
            console.print(f"• {c['message']}")
    else:
        console.print("Today: starting work")

    console.print("[dim]─────────────────────[/dim]")
    console.print()


def id_report(repo_path="."):
    """
    pulse id: כרטיס ביקור של הריפו — סיכום של הפרויקט בקופסה אחת.
    """
    repo = Repo(repo_path)
    project_name = Path(repo_path).resolve().name

    # שפה ראשית
    all_files = repo.git.ls_files().split("\n")
    all_files = [f for f in all_files if f]
    lang_counts = Counter()
    total_lines = 0

    for filepath in all_files:
        cat = get_category(filepath)
        if cat not in ("Images", "Config", "Docs", "Other"):
            lang_counts[cat] += 1
        full_path = Path(repo_path) / filepath
        if full_path.exists():
            try:
                total_lines += len(
                    full_path.read_text(encoding="utf-8", errors="replace").split("\n")
                )
            except Exception:
                pass

    top_lang = lang_counts.most_common(1)[0] if lang_counts else ("Unknown", 0)
    lang_pct = round(top_lang[1] / len(all_files) * 100) if all_files else 0

    # גיל הפרויקט — לא טוענים הכל לזיכרון
    total_commits = int(repo.git.rev_list("--count", "HEAD"))
    authors = set()
    for c in repo.iter_commits():
        authors.add(str(c.author))

    try:
        last_commit_obj = next(repo.iter_commits())
        last_commit = datetime.fromtimestamp(last_commit_obj.committed_date)
        # מוצאים את הקומיט הראשון (הכי ישן)
        first_hash = repo.git.rev_list("--max-parents=0", "HEAD").split("\n")[0]
        first_commit_obj = repo.commit(first_hash)
        first_commit = datetime.fromtimestamp(first_commit_obj.committed_date)
        age_days = (datetime.now() - first_commit).days
        if age_days > 365:
            age_str = f"{age_days // 365}y {(age_days % 365) // 30}m"
        elif age_days > 30:
            age_str = f"{age_days // 30} months"
        else:
            age_str = f"{max(age_days, 1)} {'day' if age_days <= 1 else 'days'}"
    except (StopIteration, Exception):
        age_str = "new"
        last_commit = datetime.now()

    # License
    license_file = None
    for name in ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE"]:
        if name in all_files:
            license_file = name
            break
    license_str = "MIT" if license_file else "None"

    # Version (מחפש ב-__init__.py או pyproject.toml)
    version = "—"
    for f in all_files:
        if f.endswith("__init__.py"):
            try:
                content = (Path(repo_path) / f).read_text(encoding="utf-8")
                for line in content.split("\n"):
                    if "__version__" in line and "=" in line:
                        version = line.split("=")[1].strip().strip('"').strip("'")
                        break
            except Exception:
                pass
            if version != "—":
                break

    # הצגה
    color = CATEGORY_COLORS.get(top_lang[0], "cyan")

    show_logo()
    card = (
        f"[bold {color}]{project_name}[/bold {color}]\n"
        f"\n"
        f"  Language    [{color}]{top_lang[0]} ({lang_pct}%)[/{color}]\n"
        f"  Files       {len(all_files)}\n"
        f"  Lines       {total_lines:,}\n"
        f"  Commits     {total_commits}\n"
        f"  Authors     {len(authors)}\n"
        f"  Age         {age_str}\n"
        f"  License     {license_str}\n"
        f"  Version     {version}\n"
        f"  Last commit {last_commit.strftime('%Y-%m-%d')}"
    )

    console.print(
        Panel(card, border_style=color, padding=(1, 3))
    )
    console.print()


def commit_quality_report(repo_path=".", count=100):
    """
    pulse quality: מנתח את איכות הודעות הקומיט.
    בודק: אורך, מתחיל בפועל, תיאורי, לא סתם "fix" או "update".
    """
    repo = Repo(repo_path)

    messages = []
    for commit in repo.iter_commits(max_count=count):
        msg = commit.message.strip().split("\n")[0]
        messages.append(msg)

    if not messages:
        console.print(Panel(t("no_commits"), style="yellow"))
        return

    show_logo()
    console.print(
        Panel.fit(
            f"[{th('title')}]Commit Message Quality[/{th('title')}]",
            subtitle=f"analyzing {len(messages)} commits",
            border_style=th("border"),
        )
    )

    # בדיקות
    score = 100
    checks = []

    # 1. אורך — יותר מ-10 תווים
    short = [m for m in messages if len(m) < 10]
    short_pct = round(len(short) / len(messages) * 100)
    if short_pct > 20:
        checks.append(f"[red]✗[/red] {short_pct}% are under 10 characters (too short)")
        score -= min(short_pct, 30)
    else:
        checks.append(f"[green]✓[/green] {100 - short_pct}% are over 10 characters")

    # 2. מתחיל בפועל (verb)
    verbs = ["add", "fix", "update", "remove", "refactor", "improve",
             "create", "implement", "change", "move", "rename", "delete",
             "merge", "revert", "bump", "release", "deploy", "test",
             "enable", "disable", "configure", "set", "use"]
    starts_with_verb = [
        m for m in messages
        if any(m.lower().startswith(v) for v in verbs)
    ]
    verb_pct = round(len(starts_with_verb) / len(messages) * 100)
    if verb_pct >= 60:
        checks.append(f"[green]✓[/green] {verb_pct}% start with a verb (good!)")
    else:
        checks.append(f"[yellow]![/yellow] Only {verb_pct}% start with a verb")
        score -= 15

    # 3. לא גנריות מדי
    generic = ["fix", "update", "changes", "wip", "test", "stuff", "misc", "tmp"]
    generic_msgs = [m for m in messages if m.lower().strip() in generic]
    generic_pct = round(len(generic_msgs) / len(messages) * 100)
    if generic_pct > 10:
        checks.append(
            f"[red]✗[/red] {generic_pct}% are generic "
            f"(just 'fix', 'update', 'wip'...)"
        )
        score -= min(generic_pct * 2, 25)
    else:
        checks.append(f"[green]✓[/green] {100 - generic_pct}% are descriptive")

    # 4. אורך ממוצע
    avg_len = round(sum(len(m) for m in messages) / len(messages))
    if avg_len >= 30:
        checks.append(f"[green]✓[/green] Average length: {avg_len} chars (good)")
    elif avg_len >= 15:
        checks.append(f"[yellow]![/yellow] Average length: {avg_len} chars (could be longer)")
        score -= 10
    else:
        checks.append(f"[red]✗[/red] Average length: {avg_len} chars (too short)")
        score -= 20

    # 5. Co-authored (בדיקה אם יש credit)
    coauthored = [m for m in messages if "co-authored" in m.lower()]
    if coauthored:
        checks.append(f"[green]✓[/green] {len(coauthored)} commits credit co-authors")

    score = max(score, 0)

    # הצגה
    console.print()
    for check in checks:
        console.print(f"  {check}")

    console.print()
    if score >= 80:
        color = th("positive")
        grade = "Excellent"
    elif score >= 60:
        color = "yellow"
        grade = "Good"
    elif score >= 40:
        color = "yellow"
        grade = "Needs improvement"
    else:
        color = th("negative")
        grade = "Poor"

    console.print(
        Panel(
            f"[{color}]Score: {score}/100 — {grade}[/{color}]",
            title="Commit Message Quality",
            border_style=color,
        )
    )

    # טיפים
    if score < 80:
        console.print()
        console.print("[bold]Tips:[/bold]")
        if short_pct > 20:
            console.print("  • Write what you changed AND why")
        if verb_pct < 60:
            console.print("  • Start with a verb: Add, Fix, Update, Remove...")
        if generic_pct > 10:
            console.print("  • Be specific: 'Fix login timeout' > 'fix'")
        if avg_len < 30:
            console.print("  • Aim for 30+ characters per message")
    console.print()


def code_age_report(repo_path="."):
    """
    pulse age: מראה את הגיל של כל קובץ — מתי נגעו בו לאחרונה.
    קבצים ישנים = אולי צריך לעדכן או למחוק.
    """
    repo = Repo(repo_path)
    project_name = Path(repo_path).resolve().name

    all_files = repo.git.ls_files().split("\n")
    all_files = [f for f in all_files if f]

    show_logo()
    console.print(
        Panel.fit(
            f"[{th('title')}]Code Age — {project_name}[/{th('title')}]",
            border_style=th("border"),
        )
    )

    # מוצאים מתי כל קובץ שונה לאחרונה
    file_ages = {}
    now = datetime.now()

    for filepath in all_files:
        try:
            last_commit = next(repo.iter_commits(paths=filepath, max_count=1))
            last_date = datetime.fromtimestamp(last_commit.committed_date)
            days_ago = (now - last_date).days
            file_ages[filepath] = {
                "date": last_date.strftime("%Y-%m-%d"),
                "days": days_ago,
                "author": str(last_commit.author),
            }
        except (StopIteration, Exception):
            pass

    if not file_ages:
        console.print(Panel("No file history found.", style="yellow"))
        return

    # ממיינים: הכי ישן למעלה
    sorted_files = sorted(
        file_ages.items(), key=lambda x: x[1]["days"], reverse=True
    )

    console.print()

    # ישנים (מעל 90 יום)
    stale = [(f, d) for f, d in sorted_files if d["days"] > 90]
    fresh = [(f, d) for f, d in sorted_files if d["days"] <= 7]
    medium = [(f, d) for f, d in sorted_files if 7 < d["days"] <= 90]

    if stale:
        table = Table(
            title=f"Stale Files ({len(stale)} files, 90+ days old)",
            show_header=True,
            header_style="bold red",
        )
        table.add_column("File", style="white")
        table.add_column("Last Changed", style="dim")
        table.add_column("Days Ago", justify="right", style="red")
        table.add_column("By", style="dim")

        for filepath, data in stale[:15]:
            table.add_row(
                filepath, data["date"],
                str(data["days"]), data["author"],
            )
        console.print(table)

    if medium:
        console.print()
        table2 = Table(
            title=f"Active Files ({len(medium)} files, 7-90 days)",
            show_header=True,
            header_style="bold yellow",
        )
        table2.add_column("File", style="white")
        table2.add_column("Last Changed", style="dim")
        table2.add_column("Days", justify="right", style="yellow")

        for filepath, data in medium[:10]:
            table2.add_row(filepath, data["date"], str(data["days"]))
        console.print(table2)

    if fresh:
        console.print()
        console.print(
            f"  [{th('positive')}]Fresh ({len(fresh)} files changed in last 7 days)[/{th('positive')}]"
        )

    # סיכום
    avg_age = round(
        sum(d["days"] for d in file_ages.values()) / len(file_ages)
    )
    console.print()
    console.print(f"  [bold]Average file age:[/bold] {avg_age} days")
    console.print(
        f"  [bold]Stale files:[/bold] {len(stale)} / {len(file_ages)} "
        f"({round(len(stale)/len(file_ages)*100)}%)"
    )
    console.print()


def badges_report(repo_path="."):
    """
    pulse badges: הישגים אלגנטיים מבוססי Git history.
    כל badge דורש תנאי מסוים — אם עמדת בו, הוא unlocked.
    """
    repo = Repo(repo_path)

    # אוספים נתונים
    commit_days = _get_commit_days(repo)
    streak = _calc_streak(commit_days)

    total_commits = 0
    fix_commits = 0
    add_commits = 0
    night_commits = 0
    weekend_commits = 0
    languages = set()
    files_touched = set()
    biggest_commit_files = 0

    try:
        for commit in repo.iter_commits():
            total_commits += 1
            msg = commit.message.strip().lower()
            commit_dt = datetime.fromtimestamp(commit.committed_date)

            if msg.startswith("fix"):
                fix_commits += 1
            if msg.startswith("add") or msg.startswith("create"):
                add_commits += 1
            if commit_dt.hour >= 22 or commit_dt.hour < 6:
                night_commits += 1
            if commit_dt.strftime("%A") in ("Saturday", "Sunday"):
                weekend_commits += 1

            changed = list(commit.stats.files.keys())
            biggest_commit_files = max(biggest_commit_files, len(changed))
            for f in changed:
                files_touched.add(f)
                cat = get_category(f)
                if cat not in ("Config", "Docs", "Images", "Other"):
                    languages.add(cat)
    except ValueError:
        pass

    # הגדרת badges
    badges = [
        {
            "name": "First Commit",
            "desc": "Made your first commit",
            "unlocked": total_commits >= 1,
            "icon": "·",
        },
        {
            "name": "Getting Started",
            "desc": "10+ commits",
            "unlocked": total_commits >= 10,
            "icon": "·",
        },
        {
            "name": "Centurion",
            "desc": "100+ commits",
            "unlocked": total_commits >= 100,
            "icon": "·",
        },
        {
            "name": "Bug Hunter",
            "desc": "10+ fix commits",
            "unlocked": fix_commits >= 10,
            "icon": "·",
        },
        {
            "name": "Bug Slayer",
            "desc": "50+ fix commits",
            "unlocked": fix_commits >= 50,
            "icon": "·",
        },
        {
            "name": "Creator",
            "desc": "10+ features added",
            "unlocked": add_commits >= 10,
            "icon": "·",
        },
        {
            "name": "Night Owl",
            "desc": "10+ commits after 10pm",
            "unlocked": night_commits >= 10,
            "icon": "·",
        },
        {
            "name": "Weekend Warrior",
            "desc": "10+ weekend commits",
            "unlocked": weekend_commits >= 10,
            "icon": "·",
        },
        {
            "name": "Streak Starter",
            "desc": "7-day commit streak",
            "unlocked": streak >= 7,
            "icon": "·",
        },
        {
            "name": "Marathon Runner",
            "desc": "30-day commit streak",
            "unlocked": streak >= 30,
            "icon": "·",
        },
        {
            "name": "Polyglot",
            "desc": "Code in 3+ languages",
            "unlocked": len(languages) >= 3,
            "icon": "·",
        },
        {
            "name": "Linguist",
            "desc": "Code in 5+ languages",
            "unlocked": len(languages) >= 5,
            "icon": "·",
        },
        {
            "name": "Explorer",
            "desc": "Touched 50+ files",
            "unlocked": len(files_touched) >= 50,
            "icon": "·",
        },
        {
            "name": "Architect",
            "desc": "Touched 200+ files",
            "unlocked": len(files_touched) >= 200,
            "icon": "·",
        },
        {
            "name": "Heavy Lifter",
            "desc": "Changed 20+ files in one commit",
            "unlocked": biggest_commit_files >= 20,
            "icon": "·",
        },
        {
            "name": "Consistent",
            "desc": "Active 30+ days total",
            "unlocked": len(commit_days) >= 30,
            "icon": "·",
        },
    ]

    unlocked = [b for b in badges if b["unlocked"]]
    locked = [b for b in badges if not b["unlocked"]]

    show_logo()
    console.print(
        Panel.fit(
            f"[{th('title')}]Achievements[/{th('title')}]",
            subtitle=f"{len(unlocked)}/{len(badges)} unlocked",
            border_style=th("border"),
        )
    )

    # Unlocked
    if unlocked:
        console.print()
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(width=3)
        table.add_column(style="bold", width=20)
        table.add_column(style="dim")

        for b in unlocked:
            table.add_row(
                f"[{th('positive')}]■[/{th('positive')}]",
                b["name"],
                b["desc"],
            )
        console.print(table)

    # Locked
    if locked:
        console.print()
        console.print("[dim]Locked:[/dim]")
        for b in locked:
            console.print(f"  [dim]□ {b['name']} — {b['desc']}[/dim]")

    # Stats
    console.print()
    console.print(
        f"  [bold]Stats:[/bold] {total_commits} commits · "
        f"{len(commit_days)} active days · "
        f"{len(languages)} languages · "
        f"{fix_commits} fixes"
    )
    console.print()


def leaderboard_report(repo_path=".", days=30):
    """
    pulse leaderboard: דירוג מקצועי של תורמים.
    מציג: קומיטים, קבצים, שורות, רצף — ממוין לפי קומיטים.
    """
    repo = Repo(repo_path)
    since_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

    authors = defaultdict(lambda: {
        "commits": 0, "files": set(), "insertions": 0,
        "deletions": 0, "days": set(),
    })

    try:
        for commit in repo.iter_commits():
            if commit.committed_date < since_date:
                break
            name = str(commit.author)
            authors[name]["commits"] += 1
            authors[name]["insertions"] += commit.stats.total.get("insertions", 0)
            authors[name]["deletions"] += commit.stats.total.get("deletions", 0)
            for f in commit.stats.files:
                authors[name]["files"].add(f)
            day = datetime.fromtimestamp(
                commit.committed_date
            ).strftime("%Y-%m-%d")
            authors[name]["days"].add(day)
    except ValueError:
        pass

    if not authors:
        console.print(Panel(t("no_commits"), style="yellow"))
        return

    show_logo()
    console.print(
        Panel.fit(
            f"[{th('title')}]Leaderboard[/{th('title')}] — last {days} days",
            subtitle=f"{len(authors)} {'contributor' if len(authors) == 1 else 'contributors'}",
            border_style=th("border"),
        )
    )

    table = Table(show_header=True, header_style=th("header"))
    table.add_column("Rank", style="bold", width=5)
    table.add_column("Author", style=th("accent"))
    table.add_column("Commits", justify="right")
    table.add_column("Files", justify="right")
    table.add_column("+Lines", justify="right", style=th("positive"))
    table.add_column("-Lines", justify="right", style=th("negative"))
    table.add_column("Active Days", justify="right", style="dim")

    sorted_authors = sorted(
        authors.items(),
        key=lambda x: x[1]["commits"],
        reverse=True,
    )

    for i, (name, data) in enumerate(sorted_authors, 1):
        if i == 1:
            rank = f"[bold] 1st[/bold]"
        elif i == 2:
            rank = " 2nd"
        elif i == 3:
            rank = " 3rd"
        else:
            rank = f" {i}th"

        table.add_row(
            rank,
            name,
            str(data["commits"]),
            str(len(data["files"])),
            f"+{data['insertions']}",
            f"-{data['deletions']}",
            str(len(data["days"])),
        )

    console.print()
    console.print(table)
    console.print()


def watch_dashboard(repo_path="."):
    """
    pulse watch: דשבורד חי שמתעדכן כל 10 שניות.
    מראה: קומיטים של היום, רצף, קומיט אחרון, סטטיסטיקות.
    Ctrl+C לעצור.
    """
    import time

    repo = Repo(repo_path)
    project_name = Path(repo_path).resolve().name

    console.print(
        f"[bold cyan]Watching:[/bold cyan] {project_name}\n"
        f"[dim]Refreshes every 10 seconds. Press Ctrl+C to stop.[/dim]\n"
    )

    last_head = None  # Cache: skip refresh if HEAD hasn't changed

    try:
        while True:
            # בודקים אם HEAD השתנה — אם לא, לא צריך לחשב מחדש
            current_head = repo.head.commit.hexsha if repo.head.is_valid() else None
            head_changed = current_head != last_head
            last_head = current_head

            console.clear()
            show_logo()

            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0).timestamp()

            # קומיטים של היום — git log מהיר יותר
            today_commits = []
            try:
                for commit in repo.iter_commits():
                    if commit.committed_date < today_start:
                        break
                    today_commits.append(commit)
            except ValueError:
                pass

            # רצף — uses git log --format (fast)
            commit_days = _get_commit_days(repo)
            streak = _calc_streak(commit_days)

            # קומיט אחרון
            try:
                last = next(repo.iter_commits())
                last_msg = last.message.strip().split("\n")[0]
                last_time = datetime.fromtimestamp(last.committed_date)
                mins_ago = round((now - last_time).total_seconds() / 60)
                if mins_ago < 60:
                    ago_str = f"{mins_ago}m ago"
                elif mins_ago < 1440:
                    ago_str = f"{mins_ago // 60}h ago"
                else:
                    ago_str = f"{mins_ago // 1440}d ago"
            except StopIteration:
                last_msg = "—"
                ago_str = "—"

            # Fire icon
            if streak >= 14:
                fire = "🔥🔥"
            elif streak >= 7:
                fire = "🔥"
            elif streak >= 1:
                fire = "✨"
            else:
                fire = "💤"

            # תצוגה
            console.print(
                Panel(
                    f"[bold]{project_name}[/bold]  "
                    f"[dim]{now.strftime('%H:%M:%S')}[/dim]\n\n"
                    f"  Today: [{th('accent')}]{len(today_commits)} commits[/{th('accent')}]\n"
                    f"  Streak: {fire} {streak} days\n"
                    f"  Last: [dim]{last_msg}[/dim]\n"
                    f"  [dim]({ago_str})[/dim]",
                    title="Live Dashboard",
                    border_style=th("border"),
                )
            )

            # קומיטים של היום
            if today_commits:
                console.print()
                console.print("[bold]Today's commits:[/bold]")
                for c in today_commits[:10]:
                    msg = c.message.strip().split("\n")[0]
                    t_str = datetime.fromtimestamp(
                        c.committed_date
                    ).strftime("%H:%M")
                    console.print(f"  [dim]{t_str}[/dim] {msg}")

            console.print(
                f"\n[dim]Watching... (Ctrl+C to stop)[/dim]"
            )

            time.sleep(10)

    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/dim]")
