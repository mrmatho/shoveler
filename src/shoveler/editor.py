from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal, Qt


class SqlEditor(QPlainTextEdit):
    run_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        font = QFont("Courier New", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setPlaceholderText(
            "Enter SQL here and press F5 or Ctrl+Enter to run.\n"
            "Select part of your query to run only that selection."
        )
        self.setTabStopDistance(40)

    def keyPressEvent(self, event):
        is_f5 = event.key() == Qt.Key.Key_F5
        is_ctrl_enter = (
            event.key() == Qt.Key.Key_Return
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        )
        if is_f5 or is_ctrl_enter:
            self.run_requested.emit()
        else:
            super().keyPressEvent(event)

    def get_sql(self) -> str:
        cursor = self.textCursor()
        if cursor.hasSelection():
            return cursor.selectedText()
        return self.toPlainText().strip()

    # QSyntaxHighlighter can be attached to self.document() at any point,
    # e.g. SqlHighlighter(self.document()), without changing anything here.
