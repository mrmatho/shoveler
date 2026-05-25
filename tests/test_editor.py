import os

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication, QMessageBox

from shoveler.editor import SqlEditor, SqlHighlighter
from shoveler.db_status_widget import DatabaseStatusWidget
from shoveler.main_window import MainWindow
from shoveler.query_tab import QueryTab


@pytest.fixture(scope="session")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


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