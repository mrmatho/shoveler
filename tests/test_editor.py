import os

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication, QMessageBox

from shoveler.editor import SqlEditor, SqlHighlighter
from shoveler.main_window import MainWindow


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


def test_main_window_starts_in_memory_mode(qapp):
    window = MainWindow()

    assert window.db.mode == "memory"
    assert window.db.is_connected
    assert window.save_as_action.isEnabled()
    assert "In-memory" in window.db_status.db_label.text()

    window._confirm_close_in_memory = lambda: QMessageBox.StandardButton.Discard
    window.close()


def test_main_window_close_in_memory_cancel_keeps_window_open(qapp):
    window = MainWindow()
    window._confirm_close_in_memory = lambda: QMessageBox.StandardButton.Cancel

    closed = window.close()

    assert closed is False
    assert window.db.is_connected

    window.db.close()
    window.close()


def test_main_window_close_in_memory_save_failed_keeps_window_open(qapp):
    window = MainWindow()
    window._confirm_close_in_memory = lambda: QMessageBox.StandardButton.Save
    window._save_database_as = lambda: False

    closed = window.close()

    assert closed is False
    assert window.db.is_connected

    window.db.close()
    window.close()