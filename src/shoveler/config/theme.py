from importlib import resources


DEFAULT_THEME = "light"
AVAILABLE_THEMES = ("light", "dark", "vivid")

_THEME_FILE_NAMES = {
    "light": "light.qss",
    "dark": "dark.qss",
    "vivid": "vivid.qss",
}


def normalize_theme(theme: str) -> str:
    normalized = (theme or "").strip().lower()
    if normalized in AVAILABLE_THEMES:
        return normalized
    return DEFAULT_THEME


def load_theme_stylesheet(theme: str) -> str:
    theme_name = normalize_theme(theme)
    return (
        resources.files("shoveler.assets.themes")
        .joinpath(_THEME_FILE_NAMES[theme_name])
        .read_text(encoding="utf-8")
    )
