"""
ContextPulse - Export functions: Markdown, JSON, HTML.
"""

import html as html_module
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from .config import get_category, _cat_to_hex
from .reports import group_by_category, get_hot_files, generate_summary
from .ui import console


def export_json(commits, period_label):
    """Exports the report as JSON."""
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

    print(json.dumps(output, indent=2, ensure_ascii=False))


def export_markdown(commits, period_label, output_path):
    """Exports the report to a Markdown file."""
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

    # Activity chart
    day_counts = Counter(c["date_short"] for c in commits)
    if day_counts:
        lines.append("## Daily Activity")
        max_count = max(day_counts.values())
        for day, count in sorted(day_counts.items()):
            bar_len = round(count / max_count * 20)
            bar = "█" * bar_len
            lines.append(f"- `{day}` {bar} ({count})")
        lines.append("")

    # Lines summary
    total_ins = sum(c.get("insertions", 0) for c in commits)
    total_dels = sum(c.get("deletions", 0) for c in commits)
    if total_ins > 0 or total_dels > 0:
        lines.append(
            f"**Lines:** +{total_ins} added, -{total_dels} removed "
            f"(net: {total_ins - total_dels:+d})"
        )
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


def export_html(commits, period_label, output_path):
    """Exports an HTML report with tables and styled CSS."""
    categories = group_by_category(commits)
    total_files = sum(c["files_changed"] for c in commits)
    total_ins = sum(c.get("insertions", 0) for c in commits)
    total_dels = sum(c.get("deletions", 0) for c in commits)
    authors = set(c["author"] for c in commits)
    summary = generate_summary(commits, categories)
    hot = get_hot_files(commits)
    day_counts = Counter(c["date_short"] for c in commits)

    # Bar chart in CSS
    max_day = max(day_counts.values()) if day_counts else 1
    bars_html = ""
    for day, count in sorted(day_counts.items()):
        pct = round(count / max_day * 100)
        bars_html += (
            f'<div class="bar-row">'
            f'<span class="bar-label">{day}</span>'
            f'<div class="bar" style="width:{pct}%">{count}</div>'
            f'</div>\n'
        )

    # Categories HTML
    cat_rows = ""
    sorted_cats = sorted(
        categories.items(), key=lambda x: x[1]["commits"], reverse=True
    )
    for cat_name, data in sorted_cats:
        cat_rows += (
            f"<tr><td>{cat_name}</td>"
            f"<td>{data['commits']}</td>"
            f"<td>{len(data['files'])}</td></tr>\n"
        )

    # Hot files HTML
    hot_rows = ""
    for i, (filename, count) in enumerate(hot, 1):
        fire = "🔥 " if count >= 5 else ""
        hot_rows += (
            f"<tr><td>{i}</td>"
            f"<td>{fire}{html_module.escape(filename)}</td>"
            f"<td>{count}</td></tr>\n"
        )

    # Commits HTML
    commit_rows = ""
    for c in commits:
        safe_msg = html_module.escape(c['message'])
        commit_rows += (
            f"<tr><td>{c['date']}</td>"
            f"<td><code>{c['hash']}</code></td>"
            f"<td>{safe_msg}</td>"
            f"<td>+{c.get('insertions',0)}/-{c.get('deletions',0)}</td>"
            f"<td>{c['files_changed']}</td></tr>\n"
        )

    # === Pie Chart in SVG ===
    pie_colors = [
        "#f85149", "#58a6ff", "#e3b341", "#3fb950", "#bc8cff",
        "#79c0ff", "#ff7b72", "#d2a8ff", "#56d364", "#ffa657",
    ]
    total_cat = sum(d["commits"] for d in categories.values())
    pie_slices = ""
    legend_items = ""
    offset = 0
    for i, (cat_name, data) in enumerate(sorted_cats):
        pct = data["commits"] / total_cat * 100 if total_cat > 0 else 0
        color = pie_colors[i % len(pie_colors)]
        circumference = 2 * 3.14159 * 45
        dash = pct / 100 * circumference
        gap = circumference - dash
        pie_slices += (
            f'<circle r="45" cx="60" cy="60" fill="transparent" '
            f'stroke="{color}" stroke-width="30" '
            f'stroke-dasharray="{dash:.1f} {gap:.1f}" '
            f'stroke-dashoffset="-{offset:.1f}" />\n'
        )
        offset += dash
        legend_items += (
            f'<div class="legend-item">'
            f'<span class="legend-color" style="background:{color}"></span>'
            f'{cat_name} ({pct:.0f}%)</div>\n'
        )

    # === Hour heatmap ===
    hour_counts = Counter(c.get("hour", 0) for c in commits)
    max_hour_count = max(hour_counts.values()) if hour_counts else 1
    hour_cells = ""
    for h in range(24):
        count = hour_counts.get(h, 0)
        intensity = count / max_hour_count if max_hour_count > 0 else 0
        r = int(13 + (35 - 13) * (1 - intensity))
        g = int(17 + (185 - 17) * intensity)
        b = int(23 + (54 - 23) * intensity)
        bg = f"rgb({r},{g},{b})"
        hour_cells += (
            f'<div class="hour-cell" style="background:{bg}" '
            f'title="{h:02d}:00 — {count} commits">{h}</div>\n'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ContextPulse Report — {period_label}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0d1117; color: #c9d1d9; padding: 2rem; max-width: 1000px; margin: auto; }}
  h1 {{ color: #58a6ff; margin-bottom: 0.25rem; font-size: 2rem; }}
  h2 {{ color: #58a6ff; margin: 2.5rem 0 1rem; border-bottom: 1px solid #21262d;
        padding-bottom: 0.5rem; font-size: 1.3rem; }}
  .subtitle {{ color: #8b949e; margin-bottom: 1.5rem; }}
  .summary {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px;
              padding: 1.25rem; margin: 1.5rem 0; font-size: 1.05rem; line-height: 1.6; }}
  .stats {{ display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap; }}
  .stat {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px;
           padding: 1.25rem 1rem; text-align: center; flex: 1; min-width: 120px;
           transition: transform 0.2s; }}
  .stat:hover {{ transform: translateY(-2px); border-color: #58a6ff; }}
  .stat .number {{ font-size: 2.2rem; font-weight: 700; }}
  .stat .label {{ color: #8b949e; font-size: 0.8rem; margin-top: 0.25rem; }}
  .blue {{ color: #58a6ff; }}
  .green {{ color: #3fb950; }}
  .red {{ color: #f85149; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
  th {{ background: #161b22; color: #58a6ff; text-align: left; padding: 0.75rem;
        font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; }}
  td {{ padding: 0.75rem; border-bottom: 1px solid #21262d; }}
  tr:hover {{ background: #161b22; }}
  code {{ background: #1f2937; padding: 2px 8px; border-radius: 4px; font-size: 0.85rem; color: #79c0ff; }}
  .bar-row {{ display: flex; align-items: center; margin: 0.4rem 0; }}
  .bar-label {{ width: 100px; font-size: 0.85rem; color: #8b949e; }}
  .bar {{ background: linear-gradient(90deg, #238636, #3fb950); color: white;
          padding: 6px 10px; border-radius: 4px; font-size: 0.8rem; min-width: 35px;
          transition: width 1s ease-out; }}
  .two-col {{ display: flex; gap: 2rem; align-items: flex-start; flex-wrap: wrap; }}
  .two-col > div {{ flex: 1; min-width: 280px; }}
  .pie-container {{ display: flex; align-items: center; gap: 2rem; flex-wrap: wrap; }}
  .legend-item {{ display: flex; align-items: center; gap: 0.5rem; margin: 0.3rem 0;
                  font-size: 0.9rem; }}
  .legend-color {{ width: 12px; height: 12px; border-radius: 3px; display: inline-block; }}
  .hour-grid {{ display: flex; gap: 3px; flex-wrap: wrap; margin: 0.5rem 0; }}
  .hour-cell {{ width: 38px; height: 38px; border-radius: 4px; display: flex;
                align-items: center; justify-content: center; font-size: 0.75rem;
                color: #8b949e; cursor: default; }}
  .footer {{ margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #21262d;
             color: #484f58; font-size: 0.8rem; text-align: center; }}
  .footer a {{ color: #58a6ff; text-decoration: none; }}
  @media print {{
    body {{ background: white; color: #1a1a1a; }}
    .stat {{ border: 1px solid #ddd; }}
    .stat .number {{ color: #333; }}
    .blue {{ color: #0969da; }}
    h1, h2 {{ color: #0969da; }}
    th {{ background: #f3f3f3; color: #333; }}
    td {{ border-bottom: 1px solid #eee; }}
    .summary {{ background: #f6f8fa; border-color: #ddd; }}
    .bar {{ background: #2da44e; }}
  }}
  @keyframes countUp {{ from {{ opacity: 0; transform: translateY(10px); }}
                        to {{ opacity: 1; transform: translateY(0); }} }}
  .stat {{ animation: countUp 0.5s ease-out; }}
  .stat:nth-child(2) {{ animation-delay: 0.1s; }}
  .stat:nth-child(3) {{ animation-delay: 0.2s; }}
  .stat:nth-child(4) {{ animation-delay: 0.3s; }}
  .stat:nth-child(5) {{ animation-delay: 0.4s; }}
</style>
</head>
<body>
<h1>ContextPulse</h1>
<p class="subtitle">{period_label} — generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<div class="summary">{summary}</div>

<div class="stats">
  <div class="stat"><div class="number blue">{len(commits)}</div><div class="label">Commits</div></div>
  <div class="stat"><div class="number blue">{len(authors)}</div><div class="label">Authors</div></div>
  <div class="stat"><div class="number blue">{total_files}</div><div class="label">File Changes</div></div>
  <div class="stat"><div class="number green">+{total_ins}</div><div class="label">Lines Added</div></div>
  <div class="stat"><div class="number red">-{total_dels}</div><div class="label">Lines Removed</div></div>
</div>

<h2>Category Breakdown</h2>
<div class="pie-container">
  <svg width="120" height="120" viewBox="0 0 120 120">
    {pie_slices}
  </svg>
  <div>{legend_items}</div>
</div>

<h2>Daily Activity</h2>
{bars_html}

<h2>Activity by Hour</h2>
<div class="hour-grid">
{hour_cells}
</div>

<div class="two-col">
<div>
<h2>Hot Files</h2>
<table><tr><th>#</th><th>File</th><th>Changes</th></tr>
{hot_rows}</table>
</div>
<div>
<h2>Categories</h2>
<table><tr><th>Category</th><th>Commits</th><th>Files</th></tr>
{cat_rows}</table>
</div>
</div>

<h2>Commits</h2>
<table><tr><th>Date</th><th>Hash</th><th>Message</th><th>+/-</th><th>Files</th></tr>
{commit_rows}</table>

<div class="footer">
  Generated by <a href="https://pypi.org/project/contextpulse/">ContextPulse</a>
  — <code>pip install contextpulse</code>
</div>
</body></html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    console.print(f"[green]HTML report saved to:[/green] {output_path}")
