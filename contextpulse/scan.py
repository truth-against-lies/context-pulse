"""
ContextPulse - Code scanning, learning report, multi-repo, and init config.
"""

from collections import Counter
from pathlib import Path

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError
from rich.panel import Panel
from rich.table import Table

from .config import (
    CATEGORY_COLORS, KEYWORD_TIPS, FILE_TYPE_TIPS,
    get_category, _cat_to_hex,
)
from .git_utils import get_commits
from .templates import build_learn_html
from .ui import console, show_logo


def scan_code(repo_path="."):
    """scan command: Analyzes code in repo and shows structure + quality report."""
    try:
        repo = Repo(repo_path)
    except (InvalidGitRepositoryError, NoSuchPathError):
        console.print(f"[red]Error:[/red] '{repo_path}' is not a Git repository.")
        return

    show_logo()
    console.print(
        Panel.fit(
            "[bold cyan]ContextPulse[/bold cyan] - Code Scanner",
            border_style="cyan",
        )
    )

    # === Scan all files in repo ===
    all_files = repo.git.ls_files().split("\n")
    all_files = [f for f in all_files if f]

    # === General statistics ===
    total_files = len(all_files)
    categories = Counter()
    file_sizes = {}

    for filepath in all_files:
        cat = get_category(filepath)
        categories[cat] += 1
        full_path = Path(repo_path) / filepath
        if full_path.exists():
            size = full_path.stat().st_size
            file_sizes[filepath] = size

    # === File types table ===
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

    # === Largest files ===
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

    # === Quality checks ===
    console.print()
    console.print("[bold]Quality Check[/bold]")
    issues = []
    suggestions = []

    has_readme = any(f.lower().startswith("readme") for f in all_files)
    if has_readme:
        console.print("  [green]✓[/green] README found")
    else:
        console.print("  [red]✗[/red] No README file")
        issues.append("Add a README.md to explain your project")

    has_gitignore = ".gitignore" in all_files
    if has_gitignore:
        console.print("  [green]✓[/green] .gitignore found")
    else:
        console.print("  [red]✗[/red] No .gitignore file")
        issues.append("Add .gitignore to avoid tracking unnecessary files")

    test_files = [f for f in all_files if "test" in f.lower()]
    if test_files:
        console.print(f"  [green]✓[/green] Tests found ({len(test_files)} test files)")
    else:
        console.print("  [yellow]![/yellow] No test files found")
        suggestions.append("Consider adding tests to catch bugs early")

    has_deps = any(
        f in all_files
        for f in ["requirements.txt", "pyproject.toml", "setup.py", "package.json"]
    )
    if has_deps:
        console.print("  [green]✓[/green] Dependency file found")
    else:
        console.print("  [yellow]![/yellow] No dependency file found")
        suggestions.append("Add requirements.txt or pyproject.toml")

    has_license = any(f.lower().startswith("license") for f in all_files)
    if has_license:
        console.print("  [green]✓[/green] LICENSE found")
    else:
        console.print("  [yellow]![/yellow] No LICENSE file")
        suggestions.append("Add a LICENSE file (MIT is a good default)")

    big_files = [
        f for f, s in file_sizes.items()
        if s > 1024 * 1024
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

    # === Project structure ===
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

    # === Score ===
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


def learn_report(repo_path=".", output_path="learn.html", beginner=False):
    """
    pulse learn: Creates an interactive HTML page displaying the project code.
    beginner=False -> professional version (clean, no explanations)
    beginner=True  -> beginner version (tooltips, explanations, guide)
    """
    try:
        repo = Repo(repo_path)
    except (InvalidGitRepositoryError, NoSuchPathError):
        console.print(f"[red]Error:[/red] '{repo_path}' is not a Git repository.")
        return

    all_files = repo.git.ls_files().split("\n")
    all_files = [f for f in all_files if f]

    code_extensions = set(FILE_TYPE_TIPS.keys())
    code_files = [
        f for f in all_files
        if Path(f).suffix.lower() in code_extensions
    ]

    project_name = Path(repo_path).resolve().name

    toc_html = ""
    files_html = ""

    for file_idx, filepath in enumerate(sorted(code_files)):
        full_path = Path(repo_path) / filepath
        if not full_path.exists():
            continue

        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        lines = content.split("\n")
        total_lines = len(lines)
        cat = get_category(filepath)
        suffix = Path(filepath).suffix.lower()
        file_tip = FILE_TYPE_TIPS.get(suffix, "") if beginner else ""

        # Table of contents
        toc_html += (
            f'<a href="#file-{file_idx}" class="toc-item">'
            f'<span class="toc-cat" style="color:{_cat_to_hex(cat)}">'
            f'{cat}</span> {filepath} '
            f'<span class="toc-lines">{total_lines} lines</span></a>\n'
        )

        # File analysis
        functions = []
        imports = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("async def "):
                func_name = stripped.split("(")[0].replace("def ", "").replace("async ", "")
                docstring = ""
                if i + 1 < total_lines:
                    next_lines = "\n".join(lines[i+1:i+6])
                    if '"""' in next_lines or "'''" in next_lines:
                        doc_lines = []
                        for dl in lines[i+1:i+10]:
                            doc_lines.append(dl.strip())
                            if doc_lines[-1].endswith('"""') or doc_lines[-1].endswith("'''"):
                                break
                        docstring = " ".join(
                            d.strip().strip('"').strip("'") for d in doc_lines
                        ).strip()
                functions.append({"name": func_name, "line": i + 1, "doc": docstring})
            elif stripped.startswith("class "):
                class_name = stripped.split("(")[0].split(":")[0].replace("class ", "")
                functions.append({"name": f"class {class_name}", "line": i + 1, "doc": ""})
            elif stripped.startswith("import ") or stripped.startswith("from "):
                imports.append(stripped)

        # Syntax highlighting with tooltips
        highlighted_lines = ""
        for i, line in enumerate(lines, 1):
            safe_line = (
                line.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            if beginner:
                for kw, tip in KEYWORD_TIPS.items():
                    if kw in safe_line:
                        escaped_tip = tip.replace('"', '&quot;')
                        safe_line = safe_line.replace(
                            kw,
                            f'<span class="kw" title="{escaped_tip}">{kw}</span>'
                        )
            else:
                for kw in ["def ", "class ", "import ", "from ", "return ",
                            "if ", "else:", "elif ", "for ", "while ",
                            "try:", "except ", "with ", "as ", "in ",
                            "True", "False", "None", "self"]:
                    if kw in safe_line:
                        safe_line = safe_line.replace(
                            kw, f'<span class="kw">{kw}</span>'
                        )
            # Comments
            if "#" in safe_line:
                idx = safe_line.index("#")
                before = safe_line[:idx]
                if 'title="' not in before.split(">")[-1]:
                    after = safe_line[idx:]
                    safe_line = before + f'<span class="comment">{after}</span>'

            highlighted_lines += (
                f'<div class="code-line" id="file-{file_idx}-L{i}">'
                f'<span class="line-num">{i}</span>'
                f'<span class="line-code">{safe_line}</span></div>\n'
            )

        # Functions list
        func_list = ""
        if functions:
            func_list = '<div class="func-list"><b>📋 Functions & Classes:</b><ul>'
            for fn in functions:
                doc_text = f' — <span class="func-doc">{fn["doc"]}</span>' if fn["doc"] else ""
                func_list += (
                    f'<li><a href="#file-{file_idx}-L{fn["line"]}">'
                    f'🔹 {fn["name"]}</a> '
                    f'<span class="func-line">line {fn["line"]}</span>'
                    f'{doc_text}</li>'
                )
            func_list += "</ul></div>"

        # Imports with explanations
        imports_html = ""
        if imports:
            imp_items = []
            for imp in imports[:8]:
                imp_items.append(f"<code>{imp}</code>")
            imports_html = (
                '<div class="imports-box"><b>📦 Dependencies (what this file needs):</b><br>'
                + "<br>".join(imp_items)
                + "</div>"
            )

        # File type tip
        file_tip_html = ""
        if file_tip:
            file_tip_html = f'<div class="file-tip">💡 {file_tip}</div>'

        files_html += f"""
<div class="file-block" id="file-{file_idx}">
  <div class="file-header">
    <span class="file-name">{filepath}</span>
    <span class="file-meta">{cat} · {total_lines} lines · {len(functions)} functions</span>
  </div>
  {file_tip_html}
  {imports_html}
  {func_list}
  <div class="code-block">
{highlighted_lines}
  </div>
</div>
"""

    # === Build and write HTML ===
    html = build_learn_html(project_name, len(code_files), toc_html, files_html, beginner)

    Path(output_path).write_text(html, encoding="utf-8")
    console.print(f"[green]Code guide saved to:[/green] {output_path}")
    console.print(f"[dim]Open in browser to explore your code.[/dim]")


def multi_report(base_path=".", days=7):
    """pulse multi: Scans multiple repos together and shows combined summary."""
    base = Path(base_path).resolve()

    if not base.is_dir():
        console.print(f"[red]Error:[/red] '{base_path}' is not a directory.")
        return

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
    """pulse init: Creates a .pulserc file in the repo with default settings."""
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


def changelog_report(repo_path=".", output_path=None):
    """
    pulse changelog: יוצר changelog אוטומטי מקומיטים.
    מקבץ לפי Added/Fixed/Changed/Removed לפי הודעת הקומיט.
    אם output_path ניתן — שומר לקובץ. אחרת מדפיס לטרמינל.
    """
    from datetime import datetime
    repo = Repo(repo_path)

    # מילות מפתח → קטגוריית changelog
    categories = {
        "Added": ["add", "create", "implement", "new", "introduce",
                  "support", "enable", "install", "initial", "launch"],
        "Fixed": ["fix", "resolve", "patch", "correct", "repair",
                  "bug", "hotfix", "close"],
        "Changed": ["update", "change", "modify", "improve", "enhance",
                     "refactor", "move", "rename", "upgrade", "bump",
                     "rewrite", "replace", "split", "merge", "adjust",
                     "optimize", "expand", "extend", "rework"],
        "Removed": ["remove", "delete", "drop", "deprecate", "clean",
                     "strip", "revert"],
    }

    # אוספים קומיטים לפי tags (גרסאות)
    tags = {}
    for tag in repo.tags:
        tags[tag.commit.hexsha] = str(tag)

    sections = []
    current_section = {"version": "Unreleased", "date": "", "commits": {
        "Added": [], "Fixed": [], "Changed": [], "Removed": [], "Other": [],
    }}

    for commit in repo.iter_commits():
        # בודקים אם זה tag (גרסה חדשה)
        if commit.hexsha in tags:
            if any(current_section["commits"][k] for k in current_section["commits"]):
                sections.append(current_section)
            date = datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d")
            current_section = {
                "version": tags[commit.hexsha],
                "date": date,
                "commits": {
                    "Added": [], "Fixed": [], "Changed": [], "Removed": [], "Other": [],
                },
            }

        msg = commit.message.strip().split("\n")[0]
        # מדלגים על co-authored-by ודומים
        if msg.lower().startswith("co-authored") or not msg:
            continue

        # מסווגים את הקומיט
        classified = False
        msg_lower = msg.lower()
        for cat_name, keywords in categories.items():
            if any(msg_lower.startswith(kw) for kw in keywords):
                current_section["commits"][cat_name].append(msg)
                classified = True
                break
        if not classified:
            current_section["commits"]["Other"].append(msg)

    # הוספת הסקשן האחרון
    if any(current_section["commits"][k] for k in current_section["commits"]):
        sections.append(current_section)

    # === הצגה / שמירה ===
    lines = ["# Changelog", ""]

    for section in sections:
        version = section["version"]
        date = f" ({section['date']})" if section["date"] else ""
        lines.append(f"## {version}{date}")
        lines.append("")

        for cat_name in ["Added", "Fixed", "Changed", "Removed", "Other"]:
            commits = section["commits"][cat_name]
            if commits:
                lines.append(f"### {cat_name}")
                for msg in commits:
                    lines.append(f"- {msg}")
                lines.append("")

    content = "\n".join(lines)

    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
        console.print(f"[green]Changelog saved to:[/green] {output_path}")
    else:
        console.print()
        console.print(content)
        console.print()


def install_hook(repo_path="."):
    """
    pulse hook: מתקין git hook שמראה מיני-דוח אחרי כל commit.
    יוצר קובץ .git/hooks/post-commit שמריץ pulse streak בקצרה.
    """
    repo = Repo(repo_path)
    hooks_dir = Path(repo_path) / ".git" / "hooks"

    if not hooks_dir.exists():
        console.print("[red]Error:[/red] Not a Git repository (no .git/hooks).")
        return

    hook_path = hooks_dir / "post-commit"

    # בודקים אם כבר מותקן
    if hook_path.exists():
        existing = hook_path.read_text(encoding="utf-8")
        if "contextpulse" in existing or "pulse" in existing.lower():
            console.print("[yellow]Hook already installed![/yellow]")
            console.print(f"File: {hook_path}")
            return

    hook_content = '''#!/bin/bash
# ContextPulse post-commit hook
# Shows a mini report after each commit

# Count today's commits
TODAY_COMMITS=$(git log --oneline --since="midnight" 2>/dev/null | wc -l | tr -d ' ')

# Count streak days
STREAK=0
CHECK_DATE=$(date +%Y-%m-%d)
while true; do
    COUNT=$(git log --oneline --after="$CHECK_DATE 00:00" --before="$CHECK_DATE 23:59:59" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$COUNT" -gt "0" ]; then
        STREAK=$((STREAK + 1))
        CHECK_DATE=$(date -v-1d -j -f "%Y-%m-%d" "$CHECK_DATE" +%Y-%m-%d 2>/dev/null || date -d "$CHECK_DATE -1 day" +%Y-%m-%d 2>/dev/null)
    else
        break
    fi
done

# Display
echo ""
if [ "$STREAK" -ge 7 ]; then
    echo "  🔥 Commit #$TODAY_COMMITS today! Streak: $STREAK days 🔥"
elif [ "$STREAK" -ge 3 ]; then
    echo "  ✨ Commit #$TODAY_COMMITS today! Streak: $STREAK days"
else
    echo "  👍 Commit #$TODAY_COMMITS today | Streak: $STREAK days"
fi
echo ""
'''

    hook_path.write_text(hook_content, encoding="utf-8")
    hook_path.chmod(0o755)

    console.print("[green]Git hook installed![/green]")
    console.print(f"File: {hook_path}")
    console.print()
    console.print("Now after every [cyan]git commit[/cyan], you'll see:")
    console.print("  [dim]🔥 Commit #5 today! Streak: 12 days 🔥[/dim]")
    console.print()
    console.print("[dim]To remove: delete .git/hooks/post-commit[/dim]")
