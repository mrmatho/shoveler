# Shoveler - A DuckDB Workbench

A minimal desktop SQL workbench for DuckDB, built with Python and PySide6.

Named after the [Australasian shoveler](https://en.wikipedia.org/wiki/Australasian_shoveler) - a species of "dabbling duck" - in honor of both the database's name and the app's purpose.

## Setup (uv)

```shell
git clone https://github.com/mrmatho/shoveler
cd shoveler
uv sync
```

`uv sync` creates a `.venv`, installs all dependencies including the dev group,
and respects `uv.lock` if it exists. Run it again after pulling changes.

## Running

```shell
uv run python -m shoveler
```

## Testing

```shell
uv run pytest
```

## Usage

- **Open File** — connect to an existing `.duckdb` or `.db` file (green indicator)
- **New In-Memory** — scratch database; data is lost when closed (amber indicator)
- **File > Save Database As...** — save current database state to a `.duckdb` file
- **Checkpoint** — flush the write-ahead log to disk (file databases only)
- **F5 or Ctrl+Enter** — run query
- Select part of your SQL to run only that selection
- Double-click a table name in the schema panel to insert it into the editor
- **View > Syntax highlighting** — toggle SQL highlighting on or off; enabled by default and remembered between launches

## Building a standalone Windows executable

The project includes `shoveler.spec` with the correct PyInstaller
configuration. Use this rather than running `pyinstaller` with flags directly —
the spec handles a non-obvious issue with DuckDB's compiled extension.

```shell
uv run pyinstaller shoveler.spec
```

Output is in `dist/Shoveler/`. Distribute that folder as a zip.

**Why --onedir and not --onefile?**
`--onefile` extracts everything to a temp directory on every launch, which makes
startup noticeably slow for a PySide6 app. `--onedir` is faster and easier to
debug if something goes wrong.

**Known PyInstaller issue with DuckDB:**
DuckDB's compiled core (`_duckdb.pyd` on Windows) lives outside the `duckdb/`
package directory. PyInstaller does not find it automatically. The spec file
uses `collect_all('duckdb')` which handles this correctly. If you ever regenerate
the spec from scratch, make sure this is included or the packaged app will fail
to start.

## Extending

|Feature|Where to add it|
|---|---|
|More export formats|Add menu items in `ResultsPanel._show_export_menu()` — raw data is in `_last_rows` / `_last_columns`|
