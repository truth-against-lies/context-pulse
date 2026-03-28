# ContextPulse

Turn your Git history into a human story.

ContextPulse is a CLI tool that analyzes your Git repository and generates beautiful, human-readable activity reports. Instead of reading through dozens of raw commits, get a clear summary of what happened, when, and why.

## Features

- **Smart Summary** — Automatically detects what you've been working on (bug fixes, new features, improvements)
- **Category Breakdown** — Groups changes by type (HTML, Python, JavaScript, Config, etc.) with colors
- **Hot Files** — Shows which files changed the most (your "hot spots")
- **Daily Activity Chart** — Visual bar chart showing your most active days
- **Directory Breakdown** — See which folders got the most attention (great for monorepos)
- **Multiple Time Ranges** — Today, this week, this month, custom days, or since a specific date
- **Author Filtering** — Focus on one contributor's work
- **Branch Comparison** — Compare what changed between two branches
- **Interactive Mode** — Menu-driven interface, no flags to memorize
- **Export** — Save reports as Markdown or JSON

## Installation

```bash
pip install contextpulse
```

Or install from source:

```bash
git clone https://github.com/truth-against-lies/context-pulse.git
cd context-pulse
pip install -r requirements.txt
python main.py
```

## Quick Start

```bash
# Run in any Git repository
pulse

# See today's activity
pulse --today

# Last 30 days
pulse --month

# Scan a specific repo
pulse ~/code/my-project

# Export to Markdown
pulse --export report.md

# Interactive mode (guided menu)
pulse --interactive
```

## All Options

| Flag | Short | Description |
|------|-------|-------------|
| `--today` | `-t` | Show today's commits only |
| `--days N` | `-d N` | Last N days |
| `--week` | `-w` | Last 7 days (default) |
| `--month` | `-m` | Last 30 days |
| `--since DATE` | `-s DATE` | Since a specific date (YYYY-MM-DD) |
| `--author NAME` | `-a NAME` | Filter by author name |
| `--compare A..B` | `-c A..B` | Compare two branches |
| `--export FILE` | `-e FILE` | Export report to Markdown file |
| `--json` | `-j` | Output as JSON |
| `--interactive` | `-i` | Interactive menu mode |

## Example Output

```
╭────────────────────────────────────╮
│ ContextPulse - Git Activity Report │
│ last 7 days                        │
╰──────────── 54 commits ────────────╯

╭──────────────────── Summary ─────────────────────╮
│ You made 54 commits, focusing mainly on HTML     │
│ (89%). Main activities: bug fixes, new features. │
│ Also touched: JavaScript, Style.                 │
╰──────────────────────────────────────────────────╯

       Hot Files (most changed)
┏━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ #   ┃ File             ┃ Changes ┃
┡━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ 1   │ 🔥 index.html    │      12 │
│ 2   │ 🔥 index-en.html │      11 │
│ 3   │ 🔥 sw.js         │       5 │
└─────┴──────────────────┴─────────┘

Daily Activity
  2026-03-26  ███████████████████████ 7
  2026-03-27  ██████████████████████████████ 9
```

## Requirements

- Python 3.8+
- Git installed on your system

## License

MIT
