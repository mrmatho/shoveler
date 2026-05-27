# Core Concepts

This page explains key behaviors in Shoveler so students understand what they are seeing.

## Database modes

### File-backed

- Connected to a `.duckdb` or `.db` file
- Data persists on disk
- Checkpoint is available

### In-memory

- Lives only while app is running
- Fast for experiments and classroom demos
- Data is lost on close unless saved

## Checkpoint

DuckDB can use a write-ahead log (WAL) for pending changes.

Checkpoint writes pending changes into the database file. In Shoveler, checkpoint is enabled only for file-backed databases.

## Query execution behavior

Shoveler follows this rule:

- If text is selected, run only the selection.
- If no text is selected, run all editor content.

This helps students test one statement at a time without deleting other work.

## Schema panel

The schema panel shows tables and columns from the active database.

- It refreshes after query execution when connected.
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

## Keyboard shortcuts

- `F5`: Run query
- `Ctrl+Enter`: Run query

## Themes and readability

Shoveler includes light and dark themes.

- Change via View > Theme
- Theme is saved and restored on next launch
