<p align="center">
  <pre>
   ____            _            _   ____        _
  / ___|___  _ __ | |_ _____  _| |_|  _ \ _   _| |___  ___
 | |   / _ \| '_ \| __/ _ \ \/ / __| |_) | | | | / __|/ _ \
 | |__| (_) | | | | ||  __/>  <| |_|  __/| |_| | \__ \  __/
  \____\___/|_| |_|\__\___/_/\_\\__|_|    \__,_|_|___/\___|
  </pre>
</p>

<h3 align="center">Turn your Git history into a human story</h3>

<p align="center">
  <a href="https://pypi.org/project/contextpulse/"><img src="https://img.shields.io/pypi/v/contextpulse?color=blue&label=PyPI" alt="PyPI"></a>
  <a href="https://pypi.org/project/contextpulse/"><img src="https://img.shields.io/pypi/pyversions/contextpulse" alt="Python"></a>
  <a href="https://github.com/truth-against-lies/context-pulse/blob/main/LICENSE"><img src="https://img.shields.io/github/license/truth-against-lies/context-pulse" alt="License"></a>
</p>

---

**ContextPulse** is the only CLI tool that combines Git analytics, smart summaries, team insights, work patterns, and beautiful reports — all in one package. No more juggling 5 different tools.

## Why ContextPulse?

| Feature | git-standup | git-quick-stats | onefetch | **ContextPulse** |
|---------|:-----------:|:---------------:|:--------:|:----------------:|
| Smart text summary | | | | **Yes** |
| Category breakdown | | Yes | | **Yes** |
| Hot files detection | | | | **Yes** |
| Work patterns (hours/days) | | | | **Yes** |
| Period comparison (vs) | | | | **Yes** |
| Commit streak tracker | | | | **Yes** |
| Team report | | Partial | | **Yes** |
| Multi-repo scanning | Partial | | | **Yes** |
| HTML export | | | | **Yes** |
| Hebrew support | | | | **Yes** |
| Color themes | | | Partial | **Yes** |
| Interactive mode | | Yes | | **Yes** |
| Pretty git log | | | | **Yes** |
| Project health scan | | | Partial | **Yes** |

## Installation

```bash
pip install contextpulse
```

## Quick Start

```bash
pulse                    # weekly report
pulse today              # today only
pulse month              # last 30 days
pulse scan               # project health check
pulse team               # who contributed what
pulse hours              # your work patterns
pulse vs                 # this week vs last week
pulse streak             # commit streak + calendar
pulse trends             # weekly trends over time
pulse diff               # what exactly changed
pulse blame              # who owns what + bus factor
pulse log                # pretty git log with icons
pulse learn              # code guide (HTML)
pulse learn --beginner   # code guide with explanations
pulse help               # see all commands
```

## All Commands

### Reports
| Command | Description |
|---------|-------------|
| `pulse` | Weekly activity report (default) |
| `pulse today` | Today's commits only |
| `pulse week` | Last 7 days |
| `pulse month` | Last 30 days |
| `pulse since 2026-03-01` | From a specific date |

### Analysis
| Command | Description |
|---------|-------------|
| `pulse scan` | Project health check (6 checks + score) |
| `pulse team` | Top contributors with percentages |
| `pulse hours` | Work patterns by hour and day |
| `pulse vs` | Compare current period to previous |
| `pulse streak` | Commit streak tracker + 28-day calendar |
| `pulse trends` | Weekly trends with arrows |
| `pulse diff` | Pretty diff — what exactly changed |
| `pulse blame` | Code ownership + Bus Factor |
| `pulse badges` | Your achievements (16 badges) |
| `pulse leaderboard` | Contributor ranking |
| `pulse log` | Pretty git log with smart icons |
| `pulse learn` | Generate code guide (HTML) |
| `pulse learn --beginner` | Code guide with tooltips for beginners |
| `pulse multi ~/code` | Scan all repos in a directory |
| `pulse changelog` | Auto-generate changelog |
| `pulse standup` | Standup report (paste to Slack) |
| `pulse id` | Repo identity card |
| `pulse quality` | Commit message quality score |
| `pulse age` | Code age map (stale files) |

### Options
| Flag | Short | Description |
|------|-------|-------------|
| `--days N` | `-d N` | Look back N days |
| `--author NAME` | `-a` | Filter by author |
| `--compare A..B` | `-c` | Compare two branches |
| `--export FILE` | `-e` | Export to Markdown |
| `--html FILE` | | Export to styled HTML |
| `--json` | `-j` | Output as JSON |
| `--lang he` | `-l he` | Hebrew output |
| `--theme NAME` | | Color theme (ocean/forest/sunset/minimal) |
| `--version` | `-v` | Show version |

### Options
| Flag | Short | Description |
|------|-------|-------------|
| `--accessible` | | No colors/art (screen reader friendly) |

### Setup
| Command | Description |
|---------|-------------|
| `pulse init` | Create `.pulserc` config for project defaults |
| `pulse hook` | Install post-commit mini report |
| `pulse watch` | Live dashboard (auto-refresh) |
| `pulse i` | Interactive mode (guided menu) |
| `pulse help` | Full command reference |

### Smart Mode (Natural Language)
Type freely in **Hebrew or English** — ContextPulse understands intent:
```bash
pulse מה עשיתי השבוע          # → pulse --week
pulse מי עבד השבוע             # → pulse team 7
pulse האם השתפרתי החודש        # → pulse trends 30
pulse show me the team weekly  # → pulse team 7
pulse תפתח לי לימוד מתחיל     # → pulse learn --beginner
```

## Example Output

```
   ____            _            _   ____        _
  / ___|___  _ __ | |_ _____  _| |_|  _ \ _   _| |___  ___
 | |   / _ \| '_ \| __/ _ \ \/ / __| |_) | | | | / __|/ _ \
 | |__| (_) | | | | ||  __/>  <| |_|  __/| |_| | \__ \  __/
  \____\___/|_| |_|\__\___/_/\_\\__|_|    \__,_|_|___/\___|
  Turn your Git history into a human story

╭────────────────────────────────────╮
│ ContextPulse - Git Activity Report │
│ last 7 days                        │
╰──────────── 54 commits ────────────╯

╭──────────────────────────── Summary ─────────────────────────────╮
│ You made 54 commits, focusing mainly on HTML (89%). Main         │
│ activities: bug fixes, new features. Also touched: JavaScript.   │
╰──────────────────────────────────────────────────────────────────╯

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

  +18815 lines added  -4109 lines removed  (net: +14706)

  Total: 54 commits by 1 author(s), 633 file changes
```

### Commit Streak
```
╭─────────────────────── Commit Streak ────────────────────────╮
│ 🔥 Current streak: 12 days 🔥                                │
│ On fire!                                                      │
│                                                               │
│ Best streak ever: 14 days                                     │
│ Total active days: 21                                         │
╰──────────────────────────────────────────────────────────────╯

Last 28 days:
  □ □ □ □ ■ ■ ■  ■ ■ ■ ■ ■ ■ □  ■ ■ ■ ■ ■ ■ ■  ■ ■ ■ □ ■ ■ □
```

### Work Patterns
```
Activity by Hour
  10:00  ████████████████████████ 18
  13:00  █████████████████████████ 19
  18:00  █████████████████████████ 19

  Peak hour: 18:00 (19 commits)
  Peak day: Friday (56 commits)
  Pattern: You're a afternoon coder (12-18)
```

### HTML Export
Export beautiful dark-themed HTML reports:
```bash
pulse --html report.html
```

## Requirements

- Python 3.8+
- Git installed on your system

## License

MIT

---

<p align="center">
  Made with <a href="https://claude.ai">Claude</a> + determination
</p>
