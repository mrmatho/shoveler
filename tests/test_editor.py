import os

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QKeyEvent, QTextCursor, QTextDocument
from PySide6.QtWidgets import QApplication, QListWidgetItem, QMessageBox

from shoveler.config.theme import AVAILABLE_THEMES, DEFAULT_THEME, load_theme_stylesheet, normalize_theme
from shoveler.config.text import SCHEMA_NO_FILES, results_export_scope_message
from shoveler.editor import SqlEditor, SqlHighlighter
from shoveler.db_status_widget import DatabaseStatusWidget
from shoveler.main_window import MainWindow
from shoveler.query_tab import QueryTab
from shoveler.results_panel import ResultsPanel
from shoveler.schema_panel import SchemaPanel


@pytest.fixture(scope="session")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture(autouse=True)
def close_top_level_widgets(qapp):
    yield

    for widget in qapp.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    qapp.processEvents()


def test_sql_highlighter_applies_and_clears_formats():
    document = QTextDocument()
    document.setPlainText("SELECT COUNT(*) FROM students -- comment")

    highlighter = SqlHighlighter(document)
    highlighter.rehighlight()

    formats = document.firstBlock().layout().formats()
    highlighted_tokens = {
        document.toPlainText()[entry.start : entry.start + entry.length]
        for entry in formats
    }

    assert "SELECT" in highlighted_tokens
    assert "COUNT" in highlighted_tokens
    assert "FROM" in highlighted_tokens

    highlighter.set_enabled(False)
    highlighter.rehighlight()

    assert len(document.firstBlock().layout().formats()) == 0


def test_sql_editor_enables_highlighting_by_default(qapp):
    editor = SqlEditor()

    assert editor.syntax_highlighting_enabled is True


def test_sql_editor_has_line_number_gutter(qapp):
    editor = SqlEditor()

    assert editor.line_number_area is not None
    assert editor.line_number_area_width() > 0


def test_sql_editor_line_number_gutter_width_grows_with_more_lines(qapp):
    editor = SqlEditor()
    initial_width = editor.line_number_area_width()

    editor.setPlainText("\n".join(f"SELECT {index};" for index in range(1, 201)))

    assert editor.line_number_area_width() >= initial_width


def test_sql_editor_tab_completion_prefers_keywords_over_tables_columns_and_functions(qapp):
    editor = SqlEditor()
    editor.set_completion_metadata(["sessions"], ["section"])
    editor.setPlainText("se")
    editor.moveCursor(QTextCursor.MoveOperation.End)

    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
    editor.keyPressEvent(event)

    assert editor.toPlainText() == "SELECT"


def test_sql_editor_tab_completion_prefers_tables_over_columns_and_functions(qapp):
    editor = SqlEditor()
    editor.set_completion_metadata(["customers"], ["country"])
    editor.setPlainText("cu")
    editor.moveCursor(QTextCursor.MoveOperation.End)

    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
    editor.keyPressEvent(event)

    assert editor.toPlainText() == "customers"


def test_sql_editor_tab_completion_prefers_columns_over_functions(qapp):
    editor = SqlEditor()
    editor.set_completion_metadata([], ["date_of_birth"])
    editor.setPlainText("da")
    editor.moveCursor(QTextCursor.MoveOperation.End)

    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
    editor.keyPressEvent(event)

    assert editor.toPlainText() == "date_of_birth"


def test_sql_editor_tab_with_no_completion_does_not_replace_token(qapp):
    editor = SqlEditor()
    editor.set_completion_metadata([], [])
    editor.setPlainText("zzz")
    editor.moveCursor(QTextCursor.MoveOperation.End)

    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
    editor.keyPressEvent(event)

    assert editor.toPlainText() == "zzz"


def test_sql_editor_tab_completion_includes_sql_type_names(qapp):
    editor = SqlEditor()
    editor.set_completion_metadata([], [])
    editor.setPlainText("dat")
    editor.moveCursor(QTextCursor.MoveOperation.End)

    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
    editor.keyPressEvent(event)

    assert editor.toPlainText() == "DATE"


def test_sql_editor_completion_preview_returns_ranked_candidate(qapp):
    editor = SqlEditor()
    editor.set_completion_metadata(["sessions"], ["section"])
    editor.setPlainText("sele")
    editor.moveCursor(QTextCursor.MoveOperation.End)

    assert editor._completion_preview() == ("SELECT", 0)


def test_sql_editor_completion_preview_includes_other_option_count(qapp):
    editor = SqlEditor()
    editor.set_completion_metadata(["sessions"], ["section"])
    editor.setPlainText("se")
    editor.moveCursor(QTextCursor.MoveOperation.End)

    assert editor._completion_preview() == ("SELECT", 3)


def test_sql_editor_completion_preview_is_none_for_exact_match(qapp):
    editor = SqlEditor()
    editor.set_completion_metadata([], [])
    editor.setPlainText("SELECT")
    editor.moveCursor(QTextCursor.MoveOperation.End)

    assert editor._completion_preview() is None


def test_sql_editor_completion_hint_text_with_other_options():
    assert SqlEditor._completion_hint_text("CREATE", 2) == "Tab for CREATE (or 2 other options)"


def test_sql_editor_completion_hint_uses_delay_timer(qapp):
    editor = SqlEditor()

    assert editor._completion_hint_timer.isSingleShot() is True
    assert editor._completion_hint_timer.interval() == editor._COMPLETION_HINT_DELAY_MS


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("light", "light"),
        (" DARK ", "dark"),
        ("Vivid", "vivid"),
        ("unknown", DEFAULT_THEME),
        ("", DEFAULT_THEME),
        (None, DEFAULT_THEME),
    ],
)
def test_normalize_theme_handles_valid_and_invalid_values(value, expected):
    assert normalize_theme(value) == expected


@pytest.mark.parametrize("theme", AVAILABLE_THEMES)
def test_load_theme_stylesheet_returns_qss_for_each_theme(theme):
    stylesheet = load_theme_stylesheet(theme)

    assert stylesheet
    assert "QMainWindow" in stylesheet
    assert "QPushButton" in stylesheet


def test_query_tab_load_sql_from_path_loads_editor_contents(qapp, tmp_path):
    sql_path = tmp_path / "query.sql"
    sql_text = "SELECT 1;\nSELECT 2;"
    sql_path.write_text(sql_text, encoding="utf-8")

    tab = QueryTab()
    loaded = tab._load_sql_from_path(str(sql_path))

    assert loaded is True
    assert tab.editor.toPlainText() == sql_text


def test_query_tab_load_sql_from_path_failure_returns_false(qapp, monkeypatch):
    tab = QueryTab()
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)

    loaded = tab._load_sql_from_path("does_not_exist.sql")

    assert loaded is False


def test_query_tab_show_result_forwards_column_types(qapp):
    tab = QueryTab()
    captured = {}

    def fake_show_results(columns, rows, elapsed, column_types=None):
        captured["columns"] = columns
        captured["rows"] = rows
        captured["elapsed"] = elapsed
        captured["column_types"] = column_types

    tab.results.show_results = fake_show_results

    tab.show_result(
        {
            "columns": ["price"],
            "column_types": ["DECIMAL(10,2)"],
            "rows": [(1.23,)],
            "elapsed": 0.01,
            "error": None,
        }
    )

    assert captured == {
        "columns": ["price"],
        "rows": [(1.23,)],
        "elapsed": 0.01,
        "column_types": ["DECIMAL(10,2)"],
    }


def test_results_panel_copy_to_clipboard_includes_headers_and_rows(qapp):
    panel = ResultsPanel()
    panel.show_results(["id", "name"], [(1, "Ada"), (None, "Bob")], elapsed=0.01)

    qapp.clipboard().clear()
    panel._copy_to_clipboard()

    assert qapp.clipboard().text() == "id\tname\n1\tAda\nNULL\tBob"
    panel.close()


def test_results_panel_copy_to_clipboard_can_export_selected_rows(qapp):
    panel = ResultsPanel()
    panel.show_results(["id", "name"], [(1, "Ada"), (2, "Bob"), (3, "Cat")], elapsed=0.01)
    panel.table.selectRow(1)

    qapp.clipboard().clear()
    panel._copy_to_clipboard(selected_only=True)

    assert qapp.clipboard().text() == "id\tname\n2\tBob"
    panel.close()


def test_results_panel_copy_to_clipboard_all_rows_ignores_selection(qapp):
    panel = ResultsPanel()
    panel.show_results(["id", "name"], [(1, "Ada"), (2, "Bob"), (3, "Cat")], elapsed=0.01)
    panel.table.selectRow(1)

    qapp.clipboard().clear()
    panel._copy_to_clipboard(selected_only=False)

    assert qapp.clipboard().text() == "id\tname\n1\tAda\n2\tBob\n3\tCat"
    panel.close()


def test_results_panel_export_csv_can_export_selected_rows(qapp, tmp_path, monkeypatch):
    panel = ResultsPanel()
    panel.show_results(["id", "name"], [(1, "Ada"), (2, "Bob"), (3, "Cat")], elapsed=0.01)
    panel.table.selectRow(2)

    path = tmp_path / "selected.csv"
    monkeypatch.setattr(
        "shoveler.results_panel.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(path), "CSV Files (*.csv)"),
    )

    panel._export_csv(selected_only=True)

    assert path.read_text(encoding="utf-8") == "id,name\n3,Cat\n"
    panel.close()


def test_results_panel_export_menu_has_four_explicit_actions(qapp, monkeypatch):
    panel = ResultsPanel()
    panel.show_results(["id"], [(1,)], elapsed=0.01)

    labels = []

    class FakeAction:
        def __init__(self, label):
            self.label = label
            self.enabled = True

        def setEnabled(self, enabled):
            self.enabled = enabled

    class FakeMenu:
        def __init__(self, parent=None):
            self.actions = []

        def addAction(self, label):
            labels.append(label)
            action = FakeAction(label)
            self.actions.append(action)
            return action

        def exec(self, *args, **kwargs):
            return None

    monkeypatch.setattr("shoveler.results_panel.QMenu", FakeMenu)

    panel._show_export_menu()

    assert labels == [
        "Export selected rows to CSV",
        "Copy selected rows to Clipboard",
        "Export all rows to CSV",
        "Copy all rows to Clipboard",
    ]
    panel.close()


def test_database_status_widget_shortens_long_file_path(qapp):
    widget = DatabaseStatusWidget()
    path = (
        "C:/very/long/path/to/a/database/location/that/keeps/going/"
        "and/going/example.duckdb"
    )

    widget.set_file_mode(path)

    assert widget.db_label.text() == "<b>example.duckdb</b>"
    assert widget.db_label.toolTip() == path


def test_database_status_widget_shows_short_file_path(qapp):
    widget = DatabaseStatusWidget()
    path = "C:/data/example.duckdb"

    widget.set_file_mode(path)

    assert path in widget.db_label.text()
    assert widget.db_label.toolTip() == path


def test_main_window_persists_syntax_highlighting_setting(qapp, tmp_path):
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        str(tmp_path),
    )

    window = MainWindow()
    assert window.syntax_highlighting_enabled is True

    window._set_syntax_highlighting_enabled(False)
    assert window._current_tab().editor.syntax_highlighting_enabled is False
    window._confirm_close_in_memory = lambda: QMessageBox.StandardButton.Discard
    window.close()

    reloaded = MainWindow()
    assert reloaded.syntax_highlighting_enabled is False
    assert reloaded._current_tab().editor.syntax_highlighting_enabled is False
    reloaded._confirm_close_in_memory = lambda: QMessageBox.StandardButton.Discard
    reloaded.close()


def test_main_window_theme_defaults_to_light(qapp, tmp_path):
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        str(tmp_path),
    )

    window = MainWindow()

    assert window.theme == "light"
    assert window.light_theme_action.isChecked() is True
    assert window.dark_theme_action.isChecked() is False

    window.close()


def test_main_window_persists_dark_theme_setting(qapp, tmp_path):
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        str(tmp_path),
    )

    window = MainWindow()
    window._set_theme("dark")
    window.close()

    reloaded = MainWindow()

    assert reloaded.theme == "dark"
    assert reloaded.dark_theme_action.isChecked() is True
    assert reloaded.light_theme_action.isChecked() is False

    reloaded.close()


def test_main_window_persists_vivid_theme_setting(qapp, tmp_path):
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        str(tmp_path),
    )

    window = MainWindow()
    window._set_theme("vivid")
    window.close()

    reloaded = MainWindow()

    assert reloaded.theme == "vivid"
    assert reloaded.vivid_theme_action.isChecked() is True
    assert reloaded.light_theme_action.isChecked() is False
    assert reloaded.dark_theme_action.isChecked() is False

    reloaded.close()


def test_main_window_starts_in_memory_mode(qapp):
    window = MainWindow()

    assert window.db.mode == "memory"
    assert window.db.is_connected
    assert window.save_as_action.isEnabled()
    assert "In-memory" in window.db_status.db_label.text()
    assert window.db_status.save_inline_btn.isHidden() is False

    window._confirm_close_in_memory = lambda: QMessageBox.StandardButton.Discard
    window.close()


def test_status_inline_save_button_hidden_in_file_mode(qapp, tmp_path):
    window = MainWindow()

    file_path = str(tmp_path / "test.duckdb")
    window._open_file(file_path)

    assert window.db.mode == "file"
    assert window.db_status.save_inline_btn.isHidden() is True

    window.close()


def test_main_window_close_in_memory_cancel_keeps_window_open(qapp):
    window = MainWindow()
    window.db.execute("CREATE TABLE t (x INTEGER)")
    window._confirm_close_in_memory = lambda: QMessageBox.StandardButton.Cancel

    closed = window.close()

    assert closed is False
    assert window.db.is_connected

    window.db.close()
    window.close()


def test_main_window_close_in_memory_save_failed_keeps_window_open(qapp):
    window = MainWindow()
    window.db.execute("CREATE TABLE t (x INTEGER)")
    window._confirm_close_in_memory = lambda: QMessageBox.StandardButton.Save
    window._save_database_as = lambda: False

    closed = window.close()

    assert closed is False
    assert window.db.is_connected

    window.db.close()
    window.close()


def test_main_window_close_in_memory_without_tables_skips_prompt(qapp):
    window = MainWindow()
    window._confirm_close_in_memory = lambda: pytest.fail(
        "Close confirmation should not be shown for empty in-memory database"
    )

    closed = window.close()

    assert closed is True


def test_new_memory_with_tables_cancel_keeps_existing_tables(qapp):
    window = MainWindow()
    window.db.execute("CREATE TABLE t (x INTEGER)")
    window._confirm_close_in_memory = lambda: QMessageBox.StandardButton.Cancel

    window._new_memory()

    assert "t" in window.db.get_tables()

    window.db.close()
    window.close()


def test_new_memory_with_tables_save_failed_keeps_existing_tables(qapp):
    window = MainWindow()
    window.db.execute("CREATE TABLE t (x INTEGER)")
    window._confirm_close_in_memory = lambda: QMessageBox.StandardButton.Save
    window._save_database_as = lambda: False

    window._new_memory()

    assert "t" in window.db.get_tables()

    window.db.close()
    window.close()


def test_new_memory_with_tables_discard_resets_database(qapp):
    window = MainWindow()
    window.db.execute("CREATE TABLE t (x INTEGER)")
    window._confirm_close_in_memory = lambda: QMessageBox.StandardButton.Discard

    window._new_memory()

    assert window.db.mode == "memory"
    assert window.db.get_tables() == []

    window.close()


def test_main_window_open_sql_action_uses_ctrl_o(qapp):
    window = MainWindow()

    assert window.open_sql_action.shortcut().toString() == "Ctrl+O"

    window.close()


def test_main_window_new_tab_action_uses_ctrl_t(qapp):
    window = MainWindow()

    assert window.new_tab_action.shortcut().toString() == "Ctrl+T"

    window.close()


def test_main_window_insert_file_name_inserts_into_editor(qapp):
    window = MainWindow()
    tab = window._current_tab()

    window._insert_file_name("students.csv")

    assert tab.editor.toPlainText() == "students.csv"

    window.close()


def test_schema_panel_emits_file_double_clicked(qapp):
    panel = SchemaPanel()
    emitted = []
    panel.file_double_clicked.connect(emitted.append)

    panel._on_file_double_click(QListWidgetItem("students.csv"))

    assert emitted == ["students.csv"]

    panel.close()


def test_schema_panel_ignores_no_files_placeholder_double_click(qapp):
    panel = SchemaPanel()
    emitted = []
    panel.file_double_clicked.connect(emitted.append)

    panel._on_file_double_click(QListWidgetItem(SCHEMA_NO_FILES))

    assert emitted == []

    panel.close()


def test_main_window_open_sql_routes_to_current_tab(qapp):
    window = MainWindow()
    tab = window._current_tab()
    called = {"value": False}

    def fake_open_sql_file_dialog():
        called["value"] = True
        return True

    tab.open_sql_file_dialog = fake_open_sql_file_dialog

    window._open_sql_file()

    assert called["value"] is True

    window.close()


def test_results_panel_shows_column_types_in_headers(qapp):
    panel = ResultsPanel()
    panel.show_results(
        ["price", "label", "active"],
        [(1.23, "Ada", True), (4.56, "Bob", False)],
        elapsed=0.01,
        column_types=["DECIMAL(10,2)", "VARCHAR", "BOOLEAN"],
    )

    header = panel.table.horizontalHeader()

    assert header.type_label_for_section(0) == "DECIMAL(10,2)"
    assert header.type_label_for_section(1) == "VARCHAR"
    assert header.type_label_for_section(2) == "BOOLEAN"
    assert header.badge_text_for_section(0) == "DECIMAL(10,2)"
    assert header.section_tooltip_text(1) == "Type: VARCHAR"

    panel.close()


def test_results_export_scope_message_includes_selected_and_total_counts():
    assert (
        results_export_scope_message(3, 25)
        == "3 of 25 rows selected. Export all rows or just selected rows?"
    )


def test_main_window_run_query_success_refreshes_schema_and_sets_success_status(qapp, monkeypatch):
    window = MainWindow()
    tab = window._current_tab()
    shown_results = []
    refreshed = []
    status_messages = []

    tab.show_result = lambda result: shown_results.append(result)
    monkeypatch.setattr(window.schema_panel, "refresh", lambda db: refreshed.append(db))
    monkeypatch.setattr(window.statusBar(), "showMessage", lambda message, timeout=0: status_messages.append((message, timeout)))

    fake_result = {
        "columns": ["value"],
        "column_types": ["INTEGER"],
        "rows": [(1,)],
        "elapsed": 0.01,
        "error": None,
    }
    monkeypatch.setattr(window.db, "execute", lambda sql: fake_result)

    window._run_query("SELECT 1")

    assert shown_results == [fake_result]
    assert refreshed == [window.db]
    assert status_messages[-1][1] == 4000
    assert "row" in status_messages[-1][0]

    window.close()


def test_main_window_run_query_refreshes_completion_metadata(qapp, monkeypatch):
    window = MainWindow()
    calls = []
    monkeypatch.setattr(window, "_refresh_completion_metadata", lambda: calls.append(True))

    fake_result = {
        "columns": [],
        "column_types": [],
        "rows": [],
        "elapsed": 0.01,
        "error": None,
    }
    monkeypatch.setattr(window.db, "execute", lambda sql: fake_result)

    window._run_query("SELECT 1")

    assert calls == [True]

    window.close()


def test_main_window_run_query_error_sets_error_status(qapp, monkeypatch):
    window = MainWindow()
    tab = window._current_tab()
    shown_results = []
    status_messages = []

    tab.show_result = lambda result: shown_results.append(result)
    monkeypatch.setattr(window.statusBar(), "showMessage", lambda message, timeout=0: status_messages.append((message, timeout)))

    fake_result = {
        "columns": [],
        "column_types": [],
        "rows": [],
        "elapsed": 0.01,
        "error": "syntax error",
    }
    monkeypatch.setattr(window.db, "execute", lambda sql: fake_result)

    window._run_query("BROKEN SQL")

    assert shown_results == [fake_result]
    assert status_messages[-1][1] == 5000
    assert "Error" in status_messages[-1][0]

    window.close()


def test_main_window_close_last_tab_keeps_single_tab_and_clears_editor(qapp):
    window = MainWindow()
    tab = window._current_tab()
    tab.editor.setPlainText("SELECT 1;")

    window._close_tab(0)

    assert window.tab_widget.count() == 1
    assert window._current_tab().editor.toPlainText() == ""

    window.close()


def test_main_window_open_file_failure_shows_error_dialog(qapp, monkeypatch):
    window = MainWindow()
    calls = []

    def _raise_open(path):
        raise RuntimeError("boom")

    monkeypatch.setattr(window.db, "open_file", _raise_open)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: calls.append((args, kwargs)))

    window._open_file("missing.duckdb")

    assert len(calls) == 1

    window.close()


def test_main_window_save_database_as_no_connection_shows_info(qapp, monkeypatch):
    window = MainWindow()
    calls = []
    window.db.close()
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: calls.append((args, kwargs)))

    saved = window._save_database_as()

    assert saved is False
    assert len(calls) == 1

    window.close()


def test_main_window_save_database_as_cancelled_dialog_returns_false(qapp, monkeypatch):
    window = MainWindow()
    monkeypatch.setattr(
        "shoveler.main_window.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: ("", ""),
    )

    saved = window._save_database_as()

    assert saved is False

    window.close()


def test_main_window_save_database_as_appends_duckdb_extension(qapp, monkeypatch, tmp_path):
    window = MainWindow()
    selected_without_ext = tmp_path / "my_database"
    captured = {"path": None}

    monkeypatch.setattr(
        "shoveler.main_window.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(selected_without_ext), "DuckDB Files (*.duckdb *.db)"),
    )

    def fake_save_as(path):
        captured["path"] = path
        return path

    monkeypatch.setattr(window.db, "save_as", fake_save_as)

    saved = window._save_database_as()

    assert saved is True
    assert captured["path"] == f"{selected_without_ext}.duckdb"

    window.close()


def test_query_tab_export_sql_empty_editor_shows_information(qapp, monkeypatch):
    tab = QueryTab()
    tab.editor.setPlainText("   ")
    calls = []
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: calls.append((args, kwargs)))

    tab._export_sql()

    assert len(calls) == 1

    tab.close()


def test_query_tab_export_sql_appends_sql_extension(qapp, monkeypatch, tmp_path):
    tab = QueryTab()
    tab.editor.setPlainText("SELECT 1;")
    selected_without_ext = tmp_path / "query_export"

    monkeypatch.setattr(
        "shoveler.query_tab.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(selected_without_ext), "SQL Files (*.sql)"),
    )

    tab._export_sql()

    exported_path = tmp_path / "query_export.sql"
    assert exported_path.exists()
    assert exported_path.read_text(encoding="utf-8") == "SELECT 1;"

    tab.close()


def test_query_tab_export_sql_write_failure_shows_error_dialog(qapp, monkeypatch, tmp_path):
    tab = QueryTab()
    tab.editor.setPlainText("SELECT 1;")
    calls = []

    monkeypatch.setattr(
        "shoveler.query_tab.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(tmp_path / "query.sql"), "SQL Files (*.sql)"),
    )

    def _raise_open(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("builtins.open", _raise_open)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: calls.append((args, kwargs)))

    tab._export_sql()

    assert len(calls) == 1

    tab.close()