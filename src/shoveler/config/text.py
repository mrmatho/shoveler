APP_NAME = "Shoveler"
APP_SUBTITLE = "Duck DB Workbench"
WINDOW_TITLE_BASE = f"{APP_NAME}: {APP_SUBTITLE}"

NEW_TAB_BUTTON_LABEL = "+"
NEW_TAB_BUTTON_TOOLTIP = "New query tab"
STATUS_READY = "Ready"
STATUS_SQL_FILE_LOADED = "SQL file loaded"
STATUS_IN_MEMORY_CREATED = "In-memory database created"
STATUS_CHECKPOINT_COMPLETE = "Checkpoint complete"

MENU_FILE = "&File"
MENU_VIEW = "&View"
MENU_THEME = "Theme"

ACTION_OPEN_SQL = "Open SQL..."
ACTION_SAVE_DATABASE_AS = "Save Database As..."
ACTION_SYNTAX_HIGHLIGHTING = "Syntax highlighting"
ACTION_THEME_LIGHT = "Light"
ACTION_THEME_DARK = "Dark"
ACTION_THEME_VIVID = "Vivid"

EDITOR_PLACEHOLDER = (
    "Enter SQL here and press F5 or Ctrl+Enter to run.\n"
    "Select part of your query to run only that selection."
)

SCHEMA_HEADING = "Schema"
SCHEMA_EMPTY = "Open a database\nto see its tables."
SCHEMA_FILES_HEADING = "Working Directory Files"
SCHEMA_CWD_PLACEHOLDER = "Current working directory"
SCHEMA_CHANGE_DIR = "Change..."
SCHEMA_CHANGE_DIR_TOOLTIP = "Choose a working directory"
SCHEMA_REFRESH_FILES = "Refresh"
SCHEMA_NO_FILES = "(No files in current directory)"
SCHEMA_SELECT_WORKING_DIRECTORY = "Select Working Directory"
SCHEMA_CHANGE_DIR_ERROR_TITLE = "Could not change directory"

DB_STATUS_SAVE_INLINE = "Save Database As..."
DB_STATUS_OPEN = "Open DB File"
DB_STATUS_MEMORY = "New Blank DB"
DB_STATUS_CHECKPOINT = "Checkpoint"
DB_STATUS_CHECKPOINT_TOOLTIP = "Save pending (WAL) changes to the DB file."
DB_STATUS_DISCONNECTED = "No database connected"
DB_STATUS_MEMORY_LABEL = "In-memory"
DB_STATUS_MEMORY_WARNING = "(unsaved — data is lost when closed)"
DB_STATUS_OPEN_DIALOG_TITLE = "Open DuckDB Database"
DB_STATUS_OPEN_DIALOG_FILTER = "DuckDB Files (*.duckdb *.db);;All Files (*)"
DB_STATUS_CHECKPOINT_OK = "✓"

QUERYTAB_LOAD_SQL = "Load SQL"
QUERYTAB_LOAD_SQL_TOOLTIP = "Load SQL from a .sql file"
QUERYTAB_EXPORT_SQL = "Export SQL"
QUERYTAB_EXPORT_SQL_TOOLTIP = "Export SQL in editor to a .sql file"
QUERYTAB_RUN_QUERY = "▶  Run Query"
QUERYTAB_RUN_TOOLTIP = "Run query (F5 or Ctrl+Enter). Whole query runs if no text selected."
QUERYTAB_LOAD_DIALOG_TITLE = "Load SQL"
QUERYTAB_LOAD_DIALOG_FILTER = "SQL Files (*.sql);;All Files (*)"
QUERYTAB_LOAD_FAILED = "Load failed"
QUERYTAB_EXPORT_EMPTY_TITLE = "Nothing to export"
QUERYTAB_EXPORT_EMPTY_MESSAGE = "SQL editor is empty."
QUERYTAB_EXPORT_DIALOG_TITLE = "Export SQL"
QUERYTAB_EXPORT_DEFAULT_NAME = "query.sql"
QUERYTAB_EXPORT_DIALOG_FILTER = "SQL Files (*.sql);;All Files (*)"
QUERYTAB_EXPORT_FAILED = "Export failed"

RESULTS_STATUS_EMPTY = "No results yet"
RESULTS_EXPORT_BUTTON = "Export ▾"
RESULTS_EXPORT_CSV = "Export as CSV…"
RESULTS_EXPORT_DIALOG_TITLE = "Export as CSV"
RESULTS_EXPORT_DIALOG_FILTER = "CSV Files (*.csv)"

UNSAVED_MEMORY_TITLE = "Unsaved In-Memory Database"
UNSAVED_MEMORY_TEXT = "You are using an in-memory database."
UNSAVED_MEMORY_INFO = "Data will be lost when the app closes. Save the database before closing?"

SAVE_NOTHING_TITLE = "Nothing to save"
SAVE_NOTHING_MESSAGE = "No database connected."
SAVE_DIALOG_TITLE = "Save DuckDB Database As"
SAVE_DIALOG_FILTER = "DuckDB Files (*.duckdb *.db);;All Files (*)"
OPEN_FILE_ERROR_TITLE = "Could not open file"
SAVE_FAILED_TITLE = "Save failed"
CHECKPOINT_FAILED_TITLE = "Checkpoint failed"


def window_title_with_path(path: str) -> str:
    return f"{WINDOW_TITLE_BASE} — {path}"


def window_title_in_memory() -> str:
    return f"{WINDOW_TITLE_BASE} — In-Memory"


def status_theme_set(theme: str) -> str:
    return f"Theme set to {theme}"


def status_syntax_highlighting(state: str) -> str:
    return f"Syntax highlighting {state}"


def tab_title(index: int) -> str:
    return f"Query {index}"


def status_query_error(error: str) -> str:
    return f"Error: {error}"


def status_query_ok(rows: int, elapsed: float) -> str:
    word = "row" if rows == 1 else "rows"
    return f"{rows} {word}  ·  {elapsed * 1000:.1f} ms"


def status_opened(path: str) -> str:
    return f"Opened {path}"


def status_saved(path: str) -> str:
    return f"Saved database to {path}"


def status_working_directory_set(path: str) -> str:
    return f"Working directory set to {path}"


def schema_table_insert_tooltip(table_name: str) -> str:
    return f"Double-click to insert '{table_name}' into editor"
