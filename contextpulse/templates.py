"""
HTML templates for ContextPulse reports.
"""


def build_learn_html(project_name, code_files_count, toc_html, files_html, beginner):
    """Build the full HTML string for the learn report.

    Args:
        project_name: Name of the project.
        code_files_count: Number of code files.
        toc_html: Pre-built HTML for the table of contents sidebar.
        files_html: Pre-built HTML for all file blocks.
        beginner: If True, include tooltips/explanations for beginners.

    Returns:
        Complete HTML document as a string.
    """
    title_text = "Code Guide — Beginner Mode" if beginner else "Code Guide"
    subtitle_text = (
        "Interactive code explorer — hover on colored keywords for explanations"
        if beginner
        else "Project code explorer — click functions to jump to code"
    )

    guide_section = ""
    if beginner:
        guide_section = """<div class="guide">
    <h2>🎓 How to Read This Guide</h2>
    <div class="tip"><span class="tip-icon">🔴</span>
      <span><b>Red words</b> = Python keywords (def, if, for, return...).
      <b>Hover over them</b> to see what they mean!</span></div>
    <div class="tip"><span class="tip-icon">💜</span>
      <span><b>Purple text</b> = imports (libraries/tools the file uses)</span></div>
    <div class="tip"><span class="tip-icon">⬜</span>
      <span><b>Gray italic text</b> = comments (notes the programmer left)</span></div>
    <div class="tip"><span class="tip-icon">🔹</span>
      <span><b>Function list</b> = click any function name to jump to its code</span></div>
    <div class="tip"><span class="tip-icon">💡</span>
      <span><b>Yellow tip</b> = explains what type of file this is</span></div>
    <div class="tip"><span class="tip-icon">📋</span>
      <span><b>Functions</b> = the "workers" inside each file. Each does one job.</span></div>
  </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ContextPulse Learn — {project_name}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0d1117; color: #c9d1d9; display: flex; }}

  /* === Sidebar === */
  .sidebar {{ width: 280px; background: #161b22; border-right: 1px solid #21262d;
              height: 100vh; overflow-y: auto; position: fixed; padding: 1rem; }}
  .sidebar h2 {{ color: #58a6ff; font-size: 1.1rem; margin-bottom: 1rem; }}
  .sidebar .project-name {{ color: #58a6ff; font-size: 1.3rem; font-weight: 700;
                            margin-bottom: 0.5rem; }}
  .sidebar .file-count {{ color: #8b949e; font-size: 0.85rem; margin-bottom: 1.5rem; }}
  .toc-item {{ display: block; padding: 0.4rem 0.5rem; color: #c9d1d9; text-decoration: none;
               border-radius: 4px; font-size: 0.85rem; margin: 2px 0; }}
  .toc-item:hover {{ background: #21262d; }}
  .toc-cat {{ font-size: 0.7rem; font-weight: 600; margin-right: 0.3rem; }}
  .toc-lines {{ color: #484f58; font-size: 0.75rem; }}

  /* === Main content === */
  .main {{ margin-left: 280px; padding: 2rem; flex: 1; max-width: 900px; }}

  /* === Beginner guide === */
  .guide {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px;
            padding: 1.25rem; margin-bottom: 2rem; }}
  .guide h2 {{ color: #3fb950; font-size: 1.1rem; margin-bottom: 0.75rem; border: none; }}
  .guide p {{ font-size: 0.9rem; line-height: 1.6; margin-bottom: 0.5rem; }}
  .guide .tip {{ display: flex; gap: 0.5rem; padding: 0.3rem 0; font-size: 0.85rem; }}
  .guide .tip-icon {{ font-size: 1.1rem; }}

  /* === File blocks === */
  .file-block {{ margin-bottom: 3rem; border: 1px solid #21262d; border-radius: 8px;
                 overflow: hidden; }}
  .file-header {{ background: #161b22; padding: 0.75rem 1rem; display: flex;
                  justify-content: space-between; align-items: center;
                  border-bottom: 1px solid #21262d; }}
  .file-name {{ color: #58a6ff; font-weight: 600; font-size: 1rem; }}
  .file-meta {{ color: #8b949e; font-size: 0.8rem; }}
  .file-tip {{ padding: 0.6rem 1rem; background: #1a2332; border-bottom: 1px solid #21262d;
               font-size: 0.85rem; color: #e3b341; }}
  .imports-box {{ padding: 0.75rem 1rem; background: #0d1117; border-bottom: 1px solid #21262d;
                  font-size: 0.85rem; color: #8b949e; line-height: 1.8; }}
  .imports-box code {{ background: #1f2937; padding: 2px 6px; border-radius: 3px;
                       font-size: 0.8rem; color: #bc8cff; }}
  .func-list {{ padding: 0.75rem 1rem; background: #0d1117; border-bottom: 1px solid #21262d; }}
  .func-list b {{ color: #3fb950; font-size: 0.85rem; }}
  .func-list ul {{ list-style: none; margin-top: 0.3rem; }}
  .func-list li {{ font-size: 0.85rem; padding: 0.2rem 0; }}
  .func-list a {{ color: #79c0ff; text-decoration: none; }}
  .func-list a:hover {{ text-decoration: underline; }}
  .func-line {{ color: #484f58; font-size: 0.75rem; }}
  .func-doc {{ color: #8b949e; font-style: italic; }}

  /* === Code === */
  .code-block {{ overflow-x: auto; font-family: 'SF Mono', 'Fira Code', monospace;
                 font-size: 0.82rem; line-height: 1.6; }}
  .code-line {{ display: flex; padding: 0 1rem; }}
  .code-line:hover {{ background: #161b22; }}
  .line-num {{ color: #484f58; min-width: 45px; text-align: right; padding-right: 1rem;
               user-select: none; }}
  .line-code {{ white-space: pre; }}

  /* Keywords with tooltips */
  .kw {{ color: #ff7b72; cursor: help; position: relative; }}
  .kw:hover {{ text-decoration: underline dotted; }}
  .kw[title]:hover::after {{
    content: attr(title);
    position: absolute; bottom: 100%; left: 0;
    background: #1f2937; color: #e3b341; border: 1px solid #30363d;
    padding: 8px 12px; border-radius: 6px; font-size: 0.8rem;
    white-space: normal; width: 300px; z-index: 100;
    font-family: -apple-system, sans-serif; line-height: 1.4;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
  }}
  .comment {{ color: #8b949e; font-style: italic; }}

  .footer {{ text-align: center; color: #484f58; font-size: 0.8rem; padding: 2rem;
             margin-left: 280px; }}
  .footer a {{ color: #58a6ff; text-decoration: none; }}

  @media print {{
    .sidebar {{ display: none; }}
    .main {{ margin-left: 0; }}
    body {{ background: white; color: #1a1a1a; }}
    .file-block {{ border: 1px solid #ddd; page-break-inside: avoid; }}
    .file-header {{ background: #f3f3f3; }}
    .guide {{ background: #f6f8fa; border-color: #ddd; }}
  }}
</style>
</head>
<body>
<div class="sidebar">
  <div class="project-name">📖 {project_name}</div>
  <div class="file-count">{code_files_count} code files</div>
  <h2>Files</h2>
  {toc_html}
</div>
<div class="main">
  <h1 style="color:#58a6ff; margin-bottom:0.5rem">📖 {title_text}</h1>
  <p style="color:#8b949e; margin-bottom:1.5rem">
    {subtitle_text}
  </p>

  {guide_section}

  {files_html}
</div>
<div class="footer">
  Generated by <a href="https://pypi.org/project/contextpulse/">ContextPulse</a>
  — <code>pip install contextpulse</code>
</div>
</body></html>"""
