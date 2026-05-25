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
        if (theme or "").strip().lower() == "dark":
            self._line_number_bg = QColor("#242f40")
            self._line_number_fg = QColor("#8fa1b7")
            self._line_number_border = QColor("#3b4659")
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
