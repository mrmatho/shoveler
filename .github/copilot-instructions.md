Shoveler local instructions for coding agent

Project summary
- Desktop SQL workbench for DuckDB using PySide6.
- Entrypoint is src/shoveler/__main__.py; main window wiring is in src/shoveler/main_window.py.
- Runtime architecture is thin UI widgets over a single Database service class.

How to run and validate
- Install and sync deps with: uv sync
- Run app with: uv run python -m shoveler
- Run tests with: uv run pytest
- If package metadata issues appear, ensure shoveler is installed in env and dependencies are synced. If `uv run pytest` exits non-zero, do not proceed with further changes. Report the failure output and await user instruction before continuing.

Core design rules
- Keep Database logic in src/shoveler/db.py as the single source of truth for SQL execution and schema introspection.
- UI widgets should not directly own database connections.
- MainWindow coordinates cross-widget behavior: status widget, schema refresh, query execution, and tab management.
- Preserve behavior where SQL selection is executed if highlighted; otherwise execute full editor content.
- Preserve behavior of always keeping at least one query tab open.
- Catch broad exceptions only in the outermost user-action handlers (direct UI slots/callbacks such as button clicks, menu actions, and close events) and in DB adapter edges where a user-safe fallback is needed; method size does not determine boundary status, and helper methods should not catch broadly.

Data contracts that other code relies on
- Database.execute returns a dict with exactly these keys:
  columns, rows, elapsed, error
- On error, columns and rows are empty and error is a string.
- On success, error is None and elapsed is measured in seconds.
- ResultsPanel expects rows to be iterable row tuples and columns to be ordered strings.
- If adding a new public Database method, document its return contract in this section using the same key-listing format, add deterministic unit tests in tests/test_db.py, and update docs/concepts.md if the method is user-facing.
- If Database.execute needs new or removed keys, treat it as a breaking change: update all callers in the same PR, update this section, and add a test asserting the full key set.

UI and UX conventions to preserve
- Keep status feedback in both ResultsPanel and QMainWindow status bar.
- Keep schema panel refresh after query execution when connected.
- Keep checkpoint enabled only for file-backed databases.
- Keep top status widget as the connection source of truth for current DB mode.
- Keep keyboard shortcuts F5 and Ctrl+Enter for run.

Theme and visual conventions to preserve
- Theme modes are user-selectable in View > Theme and persisted via QSettings key `ui/theme`.
- MainWindow owns global light/dark stylesheets; only add widget-level theme rules when the widget is conditionally shown and cannot receive the stylesheet from MainWindow propagation (e.g., dynamically instantiated popups).
- When theme changes, propagate it to all existing QueryTab instances and any newly created tabs.
- SqlEditor line-number gutter colors are theme-aware via `SqlEditor.set_theme`; do not use hardcoded one-theme gutter colors.
- Theme-specific widget checklist:

  | Widget / surface | Dark rule required | Light rule required | Owner |
  | --- | --- | --- | --- |
  | `QAbstractItemView` and `QHeaderView::section` | Explicitly style alternates, selection, and gridlines to avoid bright native fallback rows. | Inherit the MainWindow stylesheet unless a widget-specific override is required. | MainWindow stylesheet |
  | `QTableCornerButton::section` | Match the header styling so the top-left corner blends in. | Match the header styling so the top-left corner blends in. | MainWindow stylesheet |
  | `QDialog`, `QMessageBox`, `QInputDialog`, `QToolTip` | Style the surface so text and backgrounds stay readable. | Style the surface so text and backgrounds stay readable. | MainWindow stylesheet |
  | `SqlEditor` line-number gutter | Use `SqlEditor.set_theme`; do not hardcode one-theme gutter colors. | Use `SqlEditor.set_theme`; do not hardcode one-theme gutter colors. | SqlEditor |
  | Dark-mode row alternation | Keep it subtle so the results content stays the focus. | Use the normal light-theme alternation only if already provided by the theme. | widget/theme config |

Status/header behavior conventions
- For very long database file paths in the top status widget, display only the filename and keep full path in tooltip.
- For paths of 60 characters or fewer, show both the filename and full path inline; otherwise show only the filename and keep the full path in the tooltip.

UI regression checklist (manual)
- Run ALL applicable checklists for a given change; both the Safe change checklist and the UI regression checklist must pass when a change touches both db.py/signals and UI/theme code.
1) Launch app and switch View > Theme between Light and Dark; verify styling updates immediately for all visible widgets.
2) Open a second query tab after switching theme; verify new tab editor and gutter match active theme.
3) In dark mode, verify alternating rows are subtle (schema tree, working-directory file list, results table) and no bright native fallback rows appear.
4) Verify results table top-left corner square (`QTableCornerButton::section`) matches header colors in both themes.
5) Verify SQL line-number gutter blends with editor background and number text remains readable in both themes.
6) Open dialog surfaces (save/open/message) and hover tooltips; verify text/background contrast is correct in both themes.
7) Open DB with a short path and a very long path; verify status widget path formatting rules and tooltip behavior.
8) Run full tests with `uv run pytest` after UI/theme edits.

Coding style for this repo
- Python 3.11+ typing style is used (union with |, built-in generics where clear).
- Keep methods small and event-driven for PySide6 signal flow.
- Prefer explicit, readable control flow over abstraction.
- Catch broad exceptions only at UI boundaries or DB adapter edges where user-safe fallback is needed.
- Do not add heavy frameworks; keep dependencies minimal (PySide6 + duckdb).

Testing expectations
- Extend tests in tests/test_db.py for database behavior changes.
- Prioritize deterministic unit tests for execute/get_tables/get_columns/checkpoint behavior.
- Avoid GUI-dependent tests unless absolutely needed; current tests intentionally avoid display requirements.

Packaging and distribution notes
- Keep shoveler.spec as the canonical PyInstaller config.
- Do not switch guidance to onefile packaging; this project intentionally uses onedir.
- Preserve DuckDB packaging workaround expectations documented in README.

Documentation approach
- Keep docs lightweight and educational-first, with simple Markdown in `docs/` for GitHub Pages publishing from `/docs`.
- Phase 1 docs live in `docs/index.md`, `docs/quickstart.md`, `docs/concepts.md`, and `docs/troubleshooting.md`; keep this path-based structure stable unless explicitly reworking docs IA.
- Keep `README.md` as the short landing/onboarding page and link to the fuller docs in `docs/`.
- For feature changes, always update the relevant user docs in the same PR if UI labels, keyboard shortcuts, workflow steps, or data contract keys changed. Skip doc updates only for internal refactors with no user-visible effect.
- Prefer plain language suitable for students and teachers; include concrete steps and expected outcomes where helpful.

Safe change checklist
1) If changing db.py, verify tests still pass and contract keys are unchanged.
2) If changing signal wiring in main_window.py, verify open/new/checkpoint/run flows manually.
3) If changing results rendering/export, verify CSV export still writes headers and rows.
4) If changing schema behavior, verify double-click inserts table names into active editor.
5) If adding/changing features, proactively offer to update docs (`README.md` and `docs/` pages) and call out which pages should be touched.
