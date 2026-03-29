"""
ContextPulse - Configuration, constants, translations, and themes.
"""

from pathlib import Path

# === File-to-category mapping ===
CATEGORY_MAP = {
    ".html": "HTML", ".css": "Style", ".js": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".jsx": "JavaScript",
    ".py": "Python", ".rb": "Ruby", ".go": "Go", ".rs": "Rust",
    ".java": "Java", ".kt": "Kotlin", ".swift": "Swift",
    ".c": "C/C++", ".cpp": "C/C++", ".h": "C/C++",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".json": "Config", ".yml": "Config", ".yaml": "Config",
    ".toml": "Config", ".ini": "Config", ".env": "Config",
    ".xml": "Config", ".lock": "Config",
    ".md": "Docs", ".txt": "Docs", ".rst": "Docs",
    ".png": "Images", ".jpg": "Images", ".jpeg": "Images",
    ".svg": "Images", ".gif": "Images", ".webp": "Images", ".ico": "Images",
    ".sql": "Database", ".csv": "Data", ".parquet": "Data",
    ".test.js": "Tests", ".spec.js": "Tests", ".test.py": "Tests",
}

# === Color per category ===
CATEGORY_COLORS = {
    "HTML": "bright_red",
    "Style": "bright_blue",
    "JavaScript": "bright_yellow",
    "TypeScript": "yellow",
    "Python": "bright_green",
    "Ruby": "red",
    "Go": "cyan",
    "Rust": "bright_red",
    "Java": "red",
    "Kotlin": "magenta",
    "Swift": "bright_red",
    "C/C++": "blue",
    "Shell": "green",
    "Config": "bright_magenta",
    "Docs": "bright_white",
    "Images": "bright_cyan",
    "Database": "blue",
    "Data": "magenta",
    "Tests": "green",
    "Other": "dim",
}

# === Translations ===
TRANSLATIONS = {
    "en": {
        "starting": "starting...",
        "summary": "Summary",
        "commits": "Commits",
        "changes_by_cat": "Changes by Category",
        "hot_files": "Hot Files (most changed)",
        "changes_by_dir": "Changes by Directory",
        "daily_activity": "Daily Activity",
        "total": "Total",
        "commits_word": "commits",
        "by": "by",
        "author_s": "author(s)",
        "file_changes": "file changes",
        "lines_added": "lines added",
        "lines_removed": "lines removed",
        "net": "net",
        "no_commits": "No commits found in this period.",
        "report_title": "Git Activity Report",
        "team_report": "Team Report",
        "contributors": "Contributors",
        "work_patterns": "Work Patterns",
        "activity_by_hour": "Activity by Hour",
        "activity_by_day": "Activity by Day",
        "peak_hour": "Peak hour",
        "peak_day": "Peak day",
        "pattern": "Pattern",
        "period_comparison": "Period Comparison",
        "current": "Current",
        "previous": "Previous",
        "change": "Change",
        "productivity_up": "Productivity up!",
        "slower_period": "Slower period.",
        "same_pace": "Same pace as before.",
        "project_health": "Project Health",
        "quality_check": "Quality Check",
        "project_structure": "Project Structure",
        "file_types": "File Types in Project",
        "largest_files": "Largest Files",
        "report_saved": "Report saved to",
        "you_made": "You made",
        "focusing_on": "focusing mainly on",
        "main_activities": "Main activities",
        "also_touched": "Also touched",
        "bug_fixes": "bug fixes",
        "new_features": "new features",
        "improvements": "improvements",
        "refactoring": "refactoring",
        "testing": "testing",
        "documentation": "documentation",
        "various": "various changes",
        "morning_person": "morning person (6-12)",
        "afternoon_coder": "afternoon coder (12-18)",
        "evening_hacker": "evening hacker (18-22)",
        "night_owl": "night owl (22-06)",
        "youre_a": "You're a",
    },
    "he": {
        "starting": "מתחיל...",
        "summary": "סיכום",
        "commits": "קומיטים",
        "changes_by_cat": "שינויים לפי קטגוריה",
        "hot_files": "קבצים חמים (הכי השתנו)",
        "changes_by_dir": "שינויים לפי תיקייה",
        "daily_activity": "פעילות יומית",
        "total": "סה״כ",
        "commits_word": "קומיטים",
        "by": "ע״י",
        "author_s": "מחבר/ים",
        "file_changes": "שינויי קבצים",
        "lines_added": "שורות נוספו",
        "lines_removed": "שורות נמחקו",
        "net": "נטו",
        "no_commits": "לא נמצאו קומיטים בתקופה הזו.",
        "report_title": "דוח פעילות Git",
        "team_report": "דוח צוות",
        "contributors": "תורמים",
        "work_patterns": "דפוסי עבודה",
        "activity_by_hour": "פעילות לפי שעה",
        "activity_by_day": "פעילות לפי יום",
        "peak_hour": "שעת שיא",
        "peak_day": "יום שיא",
        "pattern": "דפוס",
        "period_comparison": "השוואת תקופות",
        "current": "נוכחי",
        "previous": "קודם",
        "change": "שינוי",
        "productivity_up": "פרודוקטיביות עלתה!",
        "slower_period": "תקופה איטית יותר.",
        "same_pace": "אותו קצב כמו קודם.",
        "project_health": "בריאות הפרויקט",
        "quality_check": "בדיקת איכות",
        "project_structure": "מבנה הפרויקט",
        "file_types": "סוגי קבצים בפרויקט",
        "largest_files": "הקבצים הגדולים ביותר",
        "report_saved": "הדוח נשמר ב",
        "you_made": "ביצעת",
        "focusing_on": "בדגש על",
        "main_activities": "פעילויות עיקריות",
        "also_touched": "גם נגעת ב",
        "bug_fixes": "תיקוני באגים",
        "new_features": "פיצ׳רים חדשים",
        "improvements": "שיפורים",
        "refactoring": "ריפקטורינג",
        "testing": "בדיקות",
        "documentation": "תיעוד",
        "various": "שינויים שונים",
        "morning_person": "אדם של בוקר (6-12)",
        "afternoon_coder": "מתכנת צהריים (12-18)",
        "evening_hacker": "האקר ערב (18-22)",
        "night_owl": "ינשוף לילה (22-06)",
        "youre_a": "אתה",
    },
}

# === Mutable global state ===
current_lang = "en"

# === Themes ===
THEMES = {
    "default": {
        "title": "bold cyan",
        "subtitle": "dim",
        "header": "bold magenta",
        "border": "cyan",
        "summary_border": "green",
        "accent": "cyan",
        "positive": "green",
        "negative": "red",
        "neutral": "dim",
    },
    "ocean": {
        "title": "bold blue",
        "subtitle": "dim cyan",
        "header": "bold cyan",
        "border": "blue",
        "summary_border": "cyan",
        "accent": "bright_blue",
        "positive": "bright_cyan",
        "negative": "bright_red",
        "neutral": "dim",
    },
    "forest": {
        "title": "bold green",
        "subtitle": "dim",
        "header": "bold bright_green",
        "border": "green",
        "summary_border": "bright_green",
        "accent": "green",
        "positive": "bright_green",
        "negative": "red",
        "neutral": "dim",
    },
    "sunset": {
        "title": "bold bright_red",
        "subtitle": "dim yellow",
        "header": "bold yellow",
        "border": "bright_red",
        "summary_border": "yellow",
        "accent": "bright_yellow",
        "positive": "yellow",
        "negative": "red",
        "neutral": "dim",
    },
    "minimal": {
        "title": "bold white",
        "subtitle": "dim",
        "header": "bold white",
        "border": "white",
        "summary_border": "white",
        "accent": "white",
        "positive": "green",
        "negative": "red",
        "neutral": "dim",
    },
}

current_theme = THEMES["default"]


# === Keyword tips for beginners ===
KEYWORD_TIPS = {
    "def ": "def = defines a function (block of reusable code). Like creating a recipe you can use again and again.",
    "class ": "class = a blueprint for creating objects. Like a cookie cutter — you define the shape once, then make many cookies.",
    "import ": "import = loads code from another file/library. Like borrowing a tool from a neighbor instead of building it yourself.",
    "from ": "from X import Y = loads a specific tool from a library. Instead of bringing the whole toolbox, you just take the screwdriver.",
    "return ": "return = sends a result back from a function. The function did its job, now it hands you the answer.",
    "if ": "if = checks a condition. 'If it's raining, take an umbrella.' The code only runs if the condition is true.",
    "else:": "else = what happens when the 'if' condition is false. 'If raining → umbrella, else → sunglasses.'",
    "elif ": "elif = 'else if' — another condition to check. Like: 'if hot → AC, elif cold → heater, else → nothing.'",
    "for ": "for = repeats code for each item in a list. Like: 'for each student in the class, check their homework.'",
    "while ": "while = keeps repeating as long as a condition is true. Like: 'while hungry, keep eating.'",
    "try:": "try = attempts to run code that might fail. Like: 'try to open the file — if it doesn't exist, handle the error gracefully.'",
    "except ": "except = catches an error from 'try'. Instead of crashing, you handle the problem. Like a safety net.",
    "with ": "with = safely opens a resource (file, connection) and auto-closes it when done. No forgetting to close!",
    "True": "True = yes, correct, on. A boolean value — the answer to a yes/no question.",
    "False": "False = no, incorrect, off. The opposite of True.",
    "None": "None = nothing, empty, no value. Like an empty box — it exists, but there's nothing inside.",
    "self": "self = refers to the current object. Like saying 'my name' — self.name means 'this object's name'.",
    "lambda": "lambda = a tiny one-line function. Instead of def + return, you write it in one line.",
}

# === File type tips ===
FILE_TYPE_TIPS = {
    ".py": "Python file — the main programming language of this project",
    ".js": "JavaScript — makes websites interactive (buttons, animations, data loading)",
    ".ts": "TypeScript — JavaScript with type safety (catches bugs before running)",
    ".html": "HTML — the structure/skeleton of a web page (headings, paragraphs, links)",
    ".css": "CSS — the styling/design of a web page (colors, fonts, layout)",
    ".json": "JSON — data format for configuration and APIs (like a structured notepad)",
    ".yml": "YAML — human-readable config format (settings, CI/CD pipelines)",
    ".yaml": "YAML — human-readable config format (settings, CI/CD pipelines)",
    ".toml": "TOML — config format popular in Python projects (pyproject.toml)",
    ".md": "Markdown — formatted text (README files, documentation)",
    ".sh": "Shell script — terminal commands saved in a file (automation)",
    ".sql": "SQL — database query language (get/insert/update data)",
    ".txt": "Plain text file",
}


def t(key):
    """Returns translated text based on the active language."""
    return TRANSLATIONS.get(current_lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )


def th(key):
    """Returns color based on the active theme."""
    return current_theme.get(key, "white")


def get_category(filename):
    """
    Returns the category for a given filename.
    Checks double extensions first (like .test.js), then single extensions.
    """
    name_lower = filename.lower()
    for ext, cat in CATEGORY_MAP.items():
        if "." in ext[1:] and name_lower.endswith(ext):
            return cat
    suffix = Path(filename).suffix.lower()
    return CATEGORY_MAP.get(suffix, "Other")


def _cat_to_hex(cat):
    """Converts category name to HEX color for HTML use."""
    color_map = {
        "HTML": "#f85149", "Style": "#58a6ff", "JavaScript": "#e3b341",
        "TypeScript": "#3178c6", "Python": "#3fb950", "Ruby": "#f85149",
        "Go": "#00add8", "Rust": "#f74c00", "Java": "#f89820",
        "Config": "#bc8cff", "Docs": "#c9d1d9", "Images": "#56d364",
        "Shell": "#3fb950", "Database": "#58a6ff", "Tests": "#3fb950",
    }
    return color_map.get(cat, "#8b949e")
