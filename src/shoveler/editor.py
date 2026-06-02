from PySide6.QtWidgets import QPlainTextEdit, QToolTip, QWidget
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)
from PySide6.QtCore import QRegularExpression, QRect, QSize, Signal, Qt
from PySide6.QtCore import QTimer

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
    _COMPLETION_HINT_DELAY_MS = 180
    _DEFAULT_FONT_SIZE = 11

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self._highlighter = SqlHighlighter(self.document())
        font = QFont("Courier New", self._DEFAULT_FONT_SIZE)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setPlaceholderText(EDITOR_PLACEHOLDER)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        line_number_palette = get_line_number_palette("light")
        self._line_number_bg = QColor(line_number_palette["background"])
        self._line_number_fg = QColor(line_number_palette["foreground"])
        self._line_number_border = QColor(line_number_palette["border"])
        self._completion_tables: list[str] = []
        self._completion_columns: list[str] = []
        self._completion_cycle_prefix: str | None = None
        self._completion_cycle_start: int | None = None
        self._completion_cycle_end: int | None = None
        self._completion_cycle_matches: list[str] = []
        self._completion_cycle_index: int = -1
        self._completion_cycle_direction: int = 1
        self._suspend_completion_tracking = False
        self._completion_hint_timer = QTimer(self)
        self._completion_hint_timer.setSingleShot(True)
        self._completion_hint_timer.setInterval(self._COMPLETION_HINT_DELAY_MS)
        self._completion_hint_timer.timeout.connect(self._show_completion_hint)
        self.set_syntax_highlighting_enabled(True)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.textChanged.connect(self._on_text_changed)
        self.cursorPositionChanged.connect(self._on_cursor_position_changed)
        self._update_line_number_area_width(0)

    def set_completion_metadata(self, table_names: list[str], column_names: list[str]):
        self._completion_tables = list(table_names)
        self._completion_columns = list(column_names)
        self._invalidate_completion_cycle()
        self._queue_completion_hint()

    @property
    def syntax_highlighting_enabled(self) -> bool:
        return self._highlighter.is_enabled

    def set_syntax_highlighting_enabled(self, enabled: bool):
        self._highlighter.set_enabled(enabled)

    def font_point_size(self) -> int:
        point_size = self.font().pointSize()
        return point_size if point_size > 0 else self._DEFAULT_FONT_SIZE

    def set_font_point_size(self, point_size: int):
        size = int(point_size)
        if self.font_point_size() == size:
            return

        font = QFont(self.font())
        font.setPointSize(size)
        self.setFont(font)
        self.line_number_area.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self._update_line_number_area_width(0)
        self.line_number_area.update()

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
        width = self.line_number_area_width()
        self.setViewportMargins(width, 0, 0, 0)

        contents_rect = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(
                contents_rect.left(),
                contents_rect.top(),
                width,
                contents_rect.height(),
            )
        )

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
        painter.setFont(self.font())

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
        is_plain_tab = (
            event.key() == Qt.Key.Key_Tab
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
        )
        is_shift_tab = (
            event.key() == Qt.Key.Key_Backtab
            or (
                event.key() == Qt.Key.Key_Tab
                and event.modifiers() == Qt.KeyboardModifier.ShiftModifier
            )
        )
        is_f5 = event.key() == Qt.Key.Key_F5
        is_ctrl_enter = (
            event.key() == Qt.Key.Key_Return
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        )
        if is_plain_tab and self._try_apply_completion(direction=1):
            return
        if is_shift_tab and self._try_apply_completion(direction=-1):
            return
        if is_f5 or is_ctrl_enter:
            self.run_requested.emit()
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event):
        self._completion_hint_timer.stop()
        self._invalidate_completion_cycle()
        QToolTip.hideText()
        super().focusOutEvent(event)

    def _on_text_changed(self):
        if not self._suspend_completion_tracking:
            self._invalidate_completion_cycle()
        self._queue_completion_hint()

    def _on_cursor_position_changed(self):
        if not self._suspend_completion_tracking and not self._completion_cycle_is_valid():
            self._invalidate_completion_cycle()
        self._queue_completion_hint()

    def get_sql(self) -> str:
        cursor = self.textCursor()
        if cursor.hasSelection():
            return cursor.selectedText()
        return self.toPlainText().strip()

    @staticmethod
    def _is_identifier_char(char: str) -> bool:
        return char.isalnum() or char == "_"

    def _completion_prefix_span(self) -> tuple[str, int, int] | None:
        cursor = self.textCursor()
        if cursor.hasSelection():
            return None

        position = cursor.position()
        block = cursor.block()
        block_text = block.text()
        in_block_position = position - block.position()

        start = in_block_position
        while start > 0 and self._is_identifier_char(block_text[start - 1]):
            start -= 1

        if start == in_block_position:
            return None

        prefix = block_text[start:in_block_position]
        start_position = block.position() + start
        return prefix, start_position, position

    def _completion_candidates(self) -> list[str]:
        # Preference order: keywords, tables, columns, types, then functions.
        ordered = [
            *SQL_KEYWORDS,
            *self._completion_tables,
            *self._completion_columns,
            *SQL_TYPE_NAMES,
            *SQL_FUNCTIONS,
        ]
        seen: set[str] = set()
        candidates: list[str] = []
        for candidate in ordered:
            key = candidate.casefold()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)
        return candidates

    def _best_completion(self, prefix: str) -> str | None:
        matches = self._completion_matches(prefix)
        if not matches:
            return None
        return matches[0]

    def _completion_matches(self, prefix: str) -> list[str]:
        key = prefix.casefold()
        return [
            candidate
            for candidate in self._completion_candidates()
            if candidate.casefold().startswith(key)
        ]

    def _invalidate_completion_cycle(self):
        self._completion_cycle_prefix = None
        self._completion_cycle_start = None
        self._completion_cycle_end = None
        self._completion_cycle_matches = []
        self._completion_cycle_index = -1
        self._completion_cycle_direction = 1

    def _completion_cycle_is_valid(self) -> bool:
        if (
            self._completion_cycle_start is None
            or self._completion_cycle_end is None
            or not self._completion_cycle_matches
            or self._completion_cycle_index < 0
            or self._completion_cycle_index >= len(self._completion_cycle_matches)
        ):
            return False

        cursor = self.textCursor()
        if cursor.hasSelection() or cursor.position() != self._completion_cycle_end:
            return False

        selection_cursor = self.textCursor()
        selection_cursor.setPosition(self._completion_cycle_start)
        selection_cursor.setPosition(
            self._completion_cycle_end,
            selection_cursor.MoveMode.KeepAnchor,
        )
        token_text = selection_cursor.selectedText()
        expected = self._completion_cycle_matches[self._completion_cycle_index]
        return token_text == expected

    def _completion_cycle_next(self, direction: int | None = None) -> tuple[str, int] | None:
        if not self._completion_cycle_is_valid() or len(self._completion_cycle_matches) <= 1:
            return None

        step = direction if direction in {-1, 1} else self._completion_cycle_direction
        next_index = (self._completion_cycle_index + step) % len(self._completion_cycle_matches)
        return self._completion_cycle_matches[next_index], next_index

    def _apply_completion_text(self, completion: str, start_position: int, end_position: int):
        cursor = self.textCursor()
        self._suspend_completion_tracking = True
        try:
            cursor.beginEditBlock()
            cursor.setPosition(start_position)
            cursor.setPosition(end_position, cursor.MoveMode.KeepAnchor)
            cursor.insertText(completion)
            cursor.endEditBlock()
            self.setTextCursor(cursor)
        finally:
            self._suspend_completion_tracking = False

    def _begin_completion_cycle(
        self,
        prefix: str,
        matches: list[str],
        selected_index: int,
        start_position: int,
    ):
        self._completion_cycle_prefix = prefix
        self._completion_cycle_matches = list(matches)
        self._completion_cycle_index = selected_index
        self._completion_cycle_start = start_position
        self._completion_cycle_end = start_position + len(matches[selected_index])

    def _completion_preview(self) -> tuple[str, int] | None:
        cycle_next = self._completion_cycle_next(self._completion_cycle_direction)
        if cycle_next is not None:
            completion, _next_index = cycle_next
            return completion, len(self._completion_cycle_matches) - 1

        completion_context = self._completion_prefix_span()
        if completion_context is None:
            return None

        prefix, _start_position, _end_position = completion_context
        matches = self._completion_matches(prefix)
        if not matches:
            return None
        completion = matches[0]
        if completion.casefold() == prefix.casefold():
            return None
        return completion, len(matches) - 1

    @staticmethod
    def _completion_hint_text(completion: str, other_options: int) -> str:
        if other_options <= 0:
            return f"Tab for {completion}"
        word = "option" if other_options == 1 else "options"
        return f"Tab for {completion} (or {other_options} other {word})"

    def _queue_completion_hint(self):
        preview = self._completion_preview()
        if not preview:
            self._completion_hint_timer.stop()
            QToolTip.hideText()
            return

        self._completion_hint_timer.start()

    def _show_completion_hint(self):
        preview = self._completion_preview()
        if not preview or not self.hasFocus():
            QToolTip.hideText()
            return
        completion, other_options = preview

        tooltip_anchor = self.mapToGlobal(self.cursorRect().bottomRight())
        QToolTip.showText(
            tooltip_anchor,
            self._completion_hint_text(completion, other_options),
            self,
        )

    def _try_apply_completion(self, direction: int = 1) -> bool:
        cycle_next = self._completion_cycle_next(direction)
        if cycle_next is not None and self._completion_cycle_start is not None and self._completion_cycle_end is not None:
            completion, next_index = cycle_next
            self._apply_completion_text(
                completion,
                self._completion_cycle_start,
                self._completion_cycle_end,
            )
            self._completion_cycle_index = next_index
            self._completion_cycle_direction = direction
            self._completion_cycle_end = self._completion_cycle_start + len(completion)
            self._completion_hint_timer.stop()
            QToolTip.hideText()
            self._queue_completion_hint()
            return True

        completion_context = self._completion_prefix_span()
        if completion_context is None:
            return False

        prefix, start_position, end_position = completion_context
        matches = self._completion_matches(prefix)
        if not matches:
            return False

        selected_index = 0 if direction >= 0 else len(matches) - 1
        completion = matches[selected_index]
        if completion.casefold() == prefix.casefold():
            if len(matches) == 1:
                return False
            selected_index = 1 if direction >= 0 else len(matches) - 2
            completion = matches[selected_index]

        self._apply_completion_text(completion, start_position, end_position)
        self._begin_completion_cycle(
            prefix=prefix,
            matches=matches,
            selected_index=selected_index,
            start_position=start_position,
        )
        self._completion_cycle_direction = direction
        self._completion_hint_timer.stop()
        QToolTip.hideText()
        self._queue_completion_hint()
        return True
