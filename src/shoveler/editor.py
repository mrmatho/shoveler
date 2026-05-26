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

from .config.syntax import (
    SQL_FUNCTIONS,
    SQL_KEYWORDS,
    SQL_TYPE_NAMES,
    get_line_number_palette,
    get_syntax_palette,
)
from .config.text import EDITOR_PLACEHOLDER


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

        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._rules.extend(
            (
                QRegularExpression(
                    rf"\b{keyword}\b",
                    QRegularExpression.PatternOption.CaseInsensitiveOption,
                ),
                self._keyword_format,
            )
            for keyword in SQL_KEYWORDS
        )
        self._rules.extend(
            (
                QRegularExpression(
                    rf"\b{type_name}\b",
                    QRegularExpression.PatternOption.CaseInsensitiveOption,
                ),
                self._type_format,
            )
            for type_name in SQL_TYPE_NAMES
        )
        self._rules.extend(
            (
                QRegularExpression(
                    rf"\b{function}\b",
                    QRegularExpression.PatternOption.CaseInsensitiveOption,
                ),
                self._function_format,
            )
            for function in SQL_FUNCTIONS
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
        palette = get_syntax_palette(theme)
        self._keyword_format.setForeground(QColor(palette["keyword"]))
        self._type_format.setForeground(QColor(palette["type"]))
        self._function_format.setForeground(QColor(palette["function"]))
        self._string_format.setForeground(QColor(palette["string"]))
        self._number_format.setForeground(QColor(palette["number"]))
        self._comment_format.setForeground(QColor(palette["comment"]))
        self._identifier_format.setForeground(QColor(palette["identifier"]))
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
        self.setPlaceholderText(EDITOR_PLACEHOLDER)
        self.setTabStopDistance(40)
        line_number_palette = get_line_number_palette("light")
        self._line_number_bg = QColor(line_number_palette["background"])
        self._line_number_fg = QColor(line_number_palette["foreground"])
        self._line_number_border = QColor(line_number_palette["border"])
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
        palette = get_line_number_palette(theme)
        self._line_number_bg = QColor(palette["background"])
        self._line_number_fg = QColor(palette["foreground"])
        self._line_number_border = QColor(palette["border"])
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
