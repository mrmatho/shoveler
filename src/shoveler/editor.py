from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)
from PySide6.QtCore import QRegularExpression, Signal, Qt


class SqlHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument):
        super().__init__(document)
        self._enabled = True

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#005cc5"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        type_format = QTextCharFormat()
        type_format.setForeground(QColor("#6f42c1"))

        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#d73a49"))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#22863a"))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b08800"))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a737d"))
        comment_format.setFontItalic(True)

        identifier_format = QTextCharFormat()
        identifier_format.setForeground(QColor("#032f62"))

        keywords = [
            "SELECT",
            "FROM",
            "WHERE",
            "GROUP",
            "BY",
            "ORDER",
            "HAVING",
            "LIMIT",
            "OFFSET",
            "JOIN",
            "INNER",
            "LEFT",
            "RIGHT",
            "FULL",
            "OUTER",
            "CROSS",
            "ON",
            "AS",
            "WITH",
            "UNION",
            "ALL",
            "DISTINCT",
            "INSERT",
            "INTO",
            "VALUES",
            "UPDATE",
            "SET",
            "DELETE",
            "CREATE",
            "ALTER",
            "DROP",
            "TABLE",
            "VIEW",
            "INDEX",
            "REPLACE",
            "OR",
            "AND",
            "NOT",
            "NULL",
            "IS",
            "LIKE",
            "IN",
            "BETWEEN",
            "CASE",
            "WHEN",
            "THEN",
            "ELSE",
            "END",
            "EXISTS",
            "PRIMARY",
            "KEY",
            "FOREIGN",
            "REFERENCES",
            "DEFAULT",
            "CHECK",
        ]
        type_names = [
            "INTEGER",
            "BIGINT",
            "SMALLINT",
            "DOUBLE",
            "DECIMAL",
            "NUMERIC",
            "REAL",
            "BOOLEAN",
            "VARCHAR",
            "TEXT",
            "TIMESTAMP",
            "DATE",
            "TIME",
            "BLOB",
        ]
        functions = [
            "COUNT",
            "SUM",
            "AVG",
            "MIN",
            "MAX",
            "COALESCE",
            "ROUND",
            "CAST",
            "NOW",
            "DATE_TRUNC",
        ]

        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._rules.extend(
            (QRegularExpression(rf"\b{keyword}\b", QRegularExpression.PatternOption.CaseInsensitiveOption), keyword_format)
            for keyword in keywords
        )
        self._rules.extend(
            (QRegularExpression(rf"\b{type_name}\b", QRegularExpression.PatternOption.CaseInsensitiveOption), type_format)
            for type_name in type_names
        )
        self._rules.extend(
            (QRegularExpression(rf"\b{function}\b", QRegularExpression.PatternOption.CaseInsensitiveOption), function_format)
            for function in functions
        )
        self._rules.extend(
            [
                (QRegularExpression(r"'([^']|'')*'"), string_format),
                (QRegularExpression(r'"[^"]+"'), identifier_format),
                (QRegularExpression(r"\b\d+(?:\.\d+)?\b"), number_format),
                (QRegularExpression(r"--[^\n]*"), comment_format),
            ]
        )

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool):
        enabled = bool(enabled)
        if self._enabled == enabled:
            return
        self._enabled = enabled
        self.rehighlight()

    def highlightBlock(self, text: str):
        if not self._enabled:
            return

        for pattern, text_format in self._rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), text_format)


class SqlEditor(QPlainTextEdit):
    run_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._highlighter = SqlHighlighter(self.document())
        font = QFont("Courier New", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setPlaceholderText(
            "Enter SQL here and press F5 or Ctrl+Enter to run.\n"
            "Select part of your query to run only that selection."
        )
        self.setTabStopDistance(40)
        self.set_syntax_highlighting_enabled(True)

    @property
    def syntax_highlighting_enabled(self) -> bool:
        return self._highlighter.is_enabled

    def set_syntax_highlighting_enabled(self, enabled: bool):
        self._highlighter.set_enabled(enabled)

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
