"""
ContextPulse - Git operations: reading commits from repositories.
"""

from datetime import datetime

from git import Repo

from .ui import console


def get_commits(repo_path=".", days=7, author_filter=None):
    """
    Reads commits from the repository.
    repo_path = path to repo ("." = current directory)
    days = how many days back (default: 7)
    author_filter = filter by author name (optional)
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
    Compares two branches and returns the commits between them.
    compare_str = "main..dev" — what's different in dev vs main
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
