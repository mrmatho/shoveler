import os

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication, QMessageBox

from shoveler.config.theme import AVAILABLE_THEMES, DEFAULT_THEME, load_theme_stylesheet, normalize_theme
from shoveler.config.text import results_export_scope_message
from shoveler.editor import SqlEditor, SqlHighlighter
from shoveler.db_status_widget import DatabaseStatusWidget
from shoveler.main_window import MainWindow
from shoveler.query_tab import QueryTab
from shoveler.results_panel import ResultsPanel


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


def test_results_panel_copy_to_clipboard_includes_headers_and_rows(qapp):
    panel = ResultsPanel()
    panel.show_results(["id", "name"], [(1, "Ada"), (None, "Bob")], elapsed=0.01)

    qapp.clipboard().clear()
    panel._copy_to_clipboard()

    assert qapp.clipboard().text() == "id\tname\n1\tAda\nNULL\tBob"


def test_results_panel_copy_to_clipboard_can_export_selected_rows(qapp):
    panel = ResultsPanel()
    panel.show_results(["id", "name"], [(1, "Ada"), (2, "Bob"), (3, "Cat")], elapsed=0.01)
    panel.table.selectRow(1)

    qapp.clipboard().clear()
    panel._copy_to_clipboard(selected_only=True)

    assert qapp.clipboard().text() == "id\tname\n2\tBob"


def test_results_panel_export_csv_can_export_selected_rows(qapp, monkeypatch, tmp_path):
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


def test_results_panel_shows_inferred_types_in_headers(qapp):
    panel = ResultsPanel()
    panel.show_results(
        ["id", "name", "active"],
        [(1, "Ada", True), (2, "Bob", False)],
        elapsed=0.01,
    )

    id_header = panel.table.horizontalHeaderItem(0)
    name_header = panel.table.horizontalHeaderItem(1)
    active_header = panel.table.horizontalHeaderItem(2)

    assert id_header is not None
    assert name_header is not None
    assert active_header is not None
    assert id_header.toolTip() == "Type: integer"
    assert name_header.toolTip() == "Type: text"
    assert active_header.toolTip() == "Type: boolean"
    assert not id_header.icon().isNull()

    panel.close()


def test_results_export_scope_message_includes_selected_and_total_counts():
    assert (
        results_export_scope_message(3, 25)
        == "3 of 25 rows selected. Export all rows or just selected rows?"
    )