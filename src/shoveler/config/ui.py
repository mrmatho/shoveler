from .theme import normalize_theme


DB_STATUS_COLOURS = {
    "file": "#2a9d2a",
    "memory": "#e6a817",
    "none": "#999999",
}

MAX_STATUS_PATH_LENGTH = 60

_DB_STATUS_SECONDARY_TEXT = {
    "light": "#6b7280",
    "dark": "#a8b5c8",
    "vivid": "#b8c6ff",
}

_SCHEMA_SECONDARY_TEXT = {
    "light": "#6b7280",
    "dark": "#9aa8bc",
    "vivid": "#a9b6ff",
}

_RESULTS_NULL_COLOURS = {
    "light": "#7d8796",
    "dark": "#93a2b8",
    "vivid": "#9eb1ff",
}

_RESULTS_STATUS_COLOURS = {
    "light": {
        "ok": "#2a9d2a",
        "error": "#cc2200",
        "neutral": "#888",
    },
    "dark": {
        "ok": "#7ed957",
        "error": "#ff8b7f",
        "neutral": "#a8b5c8",
    },
    "vivid": {
        "ok": "#8dff8a",
        "error": "#ff8ea1",
        "neutral": "#b8c3ff",
    },
}


def get_db_status_secondary_text(theme: str) -> str:
    return _DB_STATUS_SECONDARY_TEXT[normalize_theme(theme)]


def get_schema_secondary_text(theme: str) -> str:
    return _SCHEMA_SECONDARY_TEXT[normalize_theme(theme)]


def get_results_null_colour(theme: str) -> str:
    return _RESULTS_NULL_COLOURS[normalize_theme(theme)]


def get_results_status_colours(theme: str) -> dict[str, str]:
    return _RESULTS_STATUS_COLOURS[normalize_theme(theme)]
