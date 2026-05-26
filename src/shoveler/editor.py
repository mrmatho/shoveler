from PySide6.QtWidgets import QPlainTextEdit, QWidget
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)
from PySide6.QtCore import QRegularExpression, QRect, QSize, Signal, Qt


class LineNumberArea(QWidget):
    def __init__(self, editor: "SqlEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint_event(event)


class SqlHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument):
        super().__init__(document)
        self._enabled = True

        self._keyword_format = QTextCharFormat()
        self._keyword_format.setFontWeight(QFont.Weight.Bold)

        self._type_format = QTextCharFormat()

        self._function_format = QTextCharFormat()

        self._string_format = QTextCharFormat()

        self._number_format = QTextCharFormat()

        self._comment_format = QTextCharFormat()
        self._comment_format.setFontItalic(True)

        self._identifier_format = QTextCharFormat()

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
            (
                QRegularExpression(
                    rf"\b{keyword}\b",
                    QRegularExpression.PatternOption.CaseInsensitiveOption,
                ),
                self._keyword_format,
            )
            for keyword in keywords
        )
        self._rules.extend(
            (
                QRegularExpression(
                    rf"\b{type_name}\b",
                    QRegularExpression.PatternOption.CaseInsensitiveOption,
                ),
                self._type_format,
            )
            for type_name in type_names
        )
        self._rules.extend(
            (
                QRegularExpression(
                    rf"\b{function}\b",
                    QRegularExpression.PatternOption.CaseInsensitiveOption,
                ),
                self._function_format,
            )
            for function in functions
        )
        self._rules.extend(
            [
                (QRegularExpression(r"'([^']|'')*'"), self._string_format),
                (QRegularExpression(r'"[^"]+"'), self._identifier_format),
                (QRegularExpression(r"\b\d+(?:\.\d+)?\b"), self._number_format),
                (QRegularExpression(r"--[^\n]*"), self._comment_format),
            ]
        )
        self.set_theme("light")

    def set_theme(self, theme: str):
        normalized = (theme or "").strip().lower()
        if normalized == "dark":
            self._keyword_format.setForeground(QColor("#66b7ff"))
            self._type_format.setForeground(QColor("#c39aff"))
            self._function_format.setForeground(QColor("#ff8b93"))
            self._string_format.setForeground(QColor("#edb211"))
            self._number_format.setForeground(QColor("#e4b763"))
            self._comment_format.setForeground(QColor("#92a2b7"))
            self._identifier_format.setForeground(QColor("#88c8ff"))
        elif normalized == "vivid":
            self._keyword_format.setForeground(QColor("#70e6ff"))
            self._type_format.setForeground(QColor("#ff9ff3"))
            self._function_format.setForeground(QColor("#ff857a"))
            self._string_format.setForeground(QColor("#7dff98"))
            self._number_format.setForeground(QColor("#ffd86b"))
            self._comment_format.setForeground(QColor("#9cc0ff"))
            self._identifier_format.setForeground(QColor("#b693ff"))
        else:
            self._keyword_format.setForeground(QColor("#005cc5"))
            self._type_format.setForeground(QColor("#6f42c1"))
            self._function_format.setForeground(QColor("#d73a49"))
            self._string_format.setForeground(QColor("#22863a"))
            self._number_format.setForeground(QColor("#b08800"))
            self._comment_format.setForeground(QColor("#6a737d"))
            self._identifier_format.setForeground(QColor("#032f62"))
        self.rehighlight()

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
        self.line_number_area = LineNumberArea(self)
        self._highlighter = SqlHighlighter(self.document())
        font = QFont("Courier New", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setPlaceholderText(
            "Enter SQL here and press F5 or Ctrl+Enter to run.\n"
            "Select part of your query to run only that selection."
        )
        self.setTabStopDistance(40)
        self._line_number_bg = QColor("#edf3fb")
        self._line_number_fg = QColor("#70839a")
        self._line_number_border = QColor("#d7deea")
        self.set_syntax_highlighting_enabled(True)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_area_width(0)

    @property
    def syntax_highlighting_enabled(self) -> bool:
        return self._highlighter.is_enabled

    def set_syntax_highlighting_enabled(self, enabled: bool):
        self._highlighter.set_enabled(enabled)

    def set_theme(self, theme: str):
        self._highlighter.set_theme(theme)
        normalized = (theme or "").strip().lower()
        if normalized == "dark":
            self._line_number_bg = QColor("#242f40")
            self._line_number_fg = QColor("#8fa1b7")
            self._line_number_border = QColor("#3b4659")
        elif normalized == "vivid":
            self._line_number_bg = QColor("#2c2152")
            self._line_number_fg = QColor("#c4d4ff")
            self._line_number_border = QColor("#5d54a8")
        else:
            self._line_number_bg = QColor("#edf3fb")
            self._line_number_fg = QColor("#70839a")
            self._line_number_border = QColor("#d7deea")
        self.line_number_area.update()

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _block_count: int):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        contents_rect = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(
                contents_rect.left(),
                contents_rect.top(),
                self.line_number_area_width(),
                contents_rect.height(),
            )
        )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), self._line_number_bg)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(self._line_number_fg)
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

        painter.setPen(self._line_number_border)
        x = self.line_number_area.width() - 1
        painter.drawLine(x, event.rect().top(), x, event.rect().bottom())

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
