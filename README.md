# Shoveler - A DuckDB Workbench

A minimal desktop SQL workbench for DuckDB, built with Python and PySide6.

Named after the [Australasian shoveler](https://en.wikipedia.org/wiki/Australasian_shoveler) - a species of "dabbling duck" - in honor of both the database's name and the app's purpose.

## Recommended for students and teachers: download a binary

Most classroom users should use the prebuilt desktop app from GitHub Releases instead of cloning or installing with pip.

1. Open the repo's **Releases** page.
2. Download the latest desktop package for your platform.
3. Extract it and run the app.

This is the fastest path for labs and avoids Python/tooling setup on student machines.

## Mac users - install from pip

The PyInstaller-built executable is not currently signed, which leads to the downloaded app being unusable without a workaround on macOS. For Mac users, the recommended option is to install from pip until code signing and notarization are set up.

### Installation with pip

```shell
pip install shoveler
```

### Running the app

```shell
python -m shoveler
```

The remaining alternative: build from source to create a local executable with PyInstaller. This is more complex and not ideal for most users, but instructions are included in the next section.

## Setup from source (developers)

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

## Configuration layout

Shoveler now keeps most theme and UI configuration out of the widget classes.

- Theme stylesheets live in `src/shoveler/assets/themes/` as `.qss` files.
- Structured configuration lives in `src/shoveler/config/`.
- `theme.py` loads and normalizes app themes.
- `syntax.py` contains SQL highlighting keywords and per-theme editor colors.
- `ui.py` contains shared UI constants such as status colors and path thresholds.
- `text.py` contains user-facing labels, tooltips, dialog text, and status message helpers.

When adding a new theme, update both the `.qss` assets and the relevant per-theme values in `src/shoveler/config/` so editor syntax, status colors, and other theme-aware UI elements stay in sync.

## Usage

- **Open File** — connect to an existing `.duckdb` or `.db` file (green indicator)
- **New In-Memory** — scratch database; data is lost when closed (amber indicator)
- **File > Save Database As...** — save current database state to a `.duckdb` file
- **Checkpoint** — flush the write-ahead log to disk (file databases only)
- **F5 or Ctrl+Enter** — run query
- Select part of your SQL to run only that selection
- Double-click a table name in the schema panel to insert it into the editor
- **View > Syntax highlighting** — toggle SQL highlighting on or off; enabled by default and remembered between launches
- **View > Zoom** — increase, decrease, or reset font size for the editor and results panel
  - Editor: `Ctrl+=`, `Ctrl+-`, `Ctrl+0`
  - Results: `Ctrl+Shift+=`, `Ctrl+Shift+-`, `Ctrl+Shift+0`

## Documentation (Phase 1)

Basic user docs are available in the `docs/` folder:

- [Docs Home](docs/index.md)
- [Quickstart (10 minutes)](docs/quickstart.md)
- [Core Concepts](docs/concepts.md)
- [Troubleshooting](docs/troubleshooting.md)

### Publish with GitHub Pages

For a simple setup:

1. Go to repository **Settings > Pages**.
2. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
3. Choose branch `main` and folder `/docs`.
4. Save.

GitHub Pages will publish the docs automatically from the `docs/` directory.

## Building a standalone executable

The project includes `shoveler.spec` with the correct PyInstaller
configuration. Use this rather than running `pyinstaller` with flags directly —
the spec handles a non-obvious issue with DuckDB's compiled extension.

```shell
uv run pyinstaller shoveler.spec
```

Output is in `dist/Shoveler/`. Distribute that folder as a zip.

## Building and publishing desktop binaries with GitHub Actions

This repo includes a release workflow at `.github/workflows/desktop-release.yml`.

- Trigger: push a tag like `v1.2.0` (or run manually with workflow_dispatch).
- Build matrix: Windows, macOS, Linux.
- Output artifacts are intended primarily for Windows and Linux classroom distribution.
- Output artifacts:
  - `Shoveler-windows-x64.zip`
  - `Shoveler-linux-x64.tar.gz`
- Release publish: on tag pushes, artifacts are attached automatically to the GitHub Release.

### macOS note

Unsigned PyInstaller executables are not a good end-user experience on macOS. Until code signing and notarization are set up, treat macOS PyInstaller output as developer-only and avoid sharing it as a classroom distribution artifact.

### Release steps

1. Update version/changelog as needed.
2. Create and push a version tag:

```shell
git tag v1.2.0
git push origin v1.2.0
```

1. Wait for the `Desktop Release` workflow to finish.
2. Open the matching GitHub Release and verify the Windows and Linux artifacts are attached.

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
|Results table badges|Update `ResultsPanel._populate_table()` and keep export using `_last_rows` / `_last_columns` only; badge text comes from `QueryResult.column_types`|
