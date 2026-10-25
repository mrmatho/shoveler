# Core Concepts

This page explains key behaviors in Shoveler so students understand what they are seeing.

## Database modes

### File-backed

- Connected to a `.duckdb` or `.db` file
- Data persists on disk
- Checkpoint is available

![File-backed database connected in Shoveler](images/file-backed.png)

*A file-backed connection is marked with a green indicator, and Checkpoint is available.*

### In-memory

- Lives only while app is running
- Fast for experiments and classroom demos
- Data is lost on close unless saved

![In-memory database with query results](images/workbench-light.png)

*An in-memory connection is marked with an amber indicator and offers Save Database As.*

## Checkpoint

DuckDB can use a write-ahead log (WAL) for pending changes.

Checkpoint writes pending changes into the database file. In Shoveler, checkpoint is enabled only for file-backed databases.

## Query execution behavior

Shoveler follows this rule:

- If text is selected, run only the selection.
- If no text is selected, run all editor content.

This helps students test one statement at a time without deleting other work.

## Query history and unsaved SQL

Shoveler keeps the 25 most recently run SQL statements in **File > Query History**.
Choosing an entry loads it into the current editor; run it with the usual shortcut or button.

An asterisk on a query tab means its SQL has unsaved edits. Closing the tab, closing Shoveler,
or loading a history entry asks whether to save the SQL, discard the changes, or cancel.

## Schema panel

The schema panel shows tables and columns from the active database.

- It refreshes after query execution when connected.
- Use the filter above the tree to find table names, column names, or column types.
- Double-clicking a table inserts its name into the current editor.

## Results table

The results table shows a small data type badge in each column header.

- Hover the header badge to see the DuckDB logical type.
- The badge is display-only and is not included in CSV exports or clipboard copy.

## Working directory files panel

The working directory area helps students find nearby files used in labs.

- The app remembers the last working directory.
- If not available on startup, it falls back to Home/Documents when present.
- Otherwise it falls back to the home directory.
- Only files that DuckDB can import are shown: `.csv`, `.tsv`, `.parquet`, `.duckdb`, `.db`, `.sql`, `.json`, `.jsonl`, `.ndjson`, `.arrow`, `.feather`, `.xlsx`, `.xls`, `.orc`.
- Double-click a file to insert its file name into the active SQL editor.

## Keyboard shortcuts

- `F5`: Run query
- `Ctrl+Enter`: Run query
- `Ctrl+T`: New query tab
- `Ctrl+Shift+F`: Format SQL

## Formatting SQL

Click **Format SQL** (or press `Ctrl+Shift+F`) to tidy your query. Keywords become upper case, clauses such as `FROM` and `WHERE` go on their own indented lines, and common function names such as `COUNT` become upper case, column lists with more than three items are put one per line, and each statement is separated by a blank line. If you highlight some SQL, only the highlighted text is formatted.

## Invalid SQL highlighting

While you type, Shoveler asks DuckDB to check each statement (without running it). About half a second after you stop typing, a statement with a syntax error gets a red wavy underline at the problem, a red dot beside its line number, and the DuckDB message appears when you hover over it and in the status bar. Other statements in the script are not marked.

- Only syntax is checked; a misspelled table or column name is only reported when you run the query.
- Turn this off or on in **View > Highlight invalid SQL**.

## Exporting SQL

Each query tab has an **Export SQL** button that saves the current editor content to a `.sql` file.

- If the editor is empty, an information dialog is shown instead.
- The `.sql` extension is appended automatically if not included in the chosen filename.
- If the file cannot be written, an error dialog is shown.

## Themes and readability

Shoveler includes light and dark themes.

- Change via View > Theme
- Theme is saved and restored on next launch

![Shoveler using its dark theme](images/workbench-dark.png)

*The editor, schema, and results areas all follow the selected theme.*
