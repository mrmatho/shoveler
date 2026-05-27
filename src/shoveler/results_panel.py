import csv
from datetime import date, datetime, time as time_type
from decimal import Decimal

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QPushButton,
    QMenu,
    QFileDialog,
    QHeaderView,
    QToolTip,
    QStyle,
    QStyleOptionHeader,
)
from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QFont, QFontMetrics, QPen, QPalette

from .config.text import (
    RESULTS_EXPORT_BUTTON,
    RESULTS_EXPORT_ALL_CLIPBOARD,
    RESULTS_EXPORT_ALL_CSV,
    RESULTS_EXPORT_DIALOG_FILTER,
    RESULTS_EXPORT_DIALOG_TITLE,
    RESULTS_STATUS_EMPTY,
    RESULTS_EXPORT_SELECTED_CLIPBOARD,
    RESULTS_EXPORT_SELECTED_CSV,
)
from .config.ui import get_results_null_colour, get_results_status_colours


class ResultsHeaderView(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self._column_types: list[str] = []
        self._theme = "light"
        self.setMouseTracking(True)

    def set_theme(self, theme: str):
        self._theme = (theme or "").strip().lower()
        self.viewport().update()

    def set_column_types(self, column_types: list[str]):
        self._column_types = list(column_types)
        self.viewport().update()
        self.updateGeometry()

    def type_label_for_section(self, logical_index: int) -> str:
        if 0 <= logical_index < len(self._column_types):
            return self._column_types[logical_index]
        return "UNKNOWN"

    def badge_text_for_section(self, logical_index: int) -> str:
        return self.type_label_for_section(logical_index)

    def section_tooltip_text(self, logical_index: int) -> str:
        return f"Type: {self.type_label_for_section(logical_index)}"

    def sectionSizeFromContents(self, logical_index: int) -> QSize:
        size = super().sectionSizeFromContents(logical_index)
        badge_text = self.badge_text_for_section(logical_index)
        if not badge_text:
            return size

        badge_font = self._badge_font()
        badge_metrics = QFontMetrics(badge_font)
        badge_width = badge_metrics.horizontalAdvance(badge_text) + 14
        badge_height = badge_metrics.height() + 8
        return QSize(size.width() + badge_width + 10, max(size.height(), badge_height))

    def paintSection(self, painter, rect, logical_index):
        if not rect.isValid():
            return

        option = QStyleOptionHeader()
        self.initStyleOption(option)
        option.rect = rect
        option.text = ""
        option.icon = QIcon()

        painter.save()
        self.style().drawControl(QStyle.ControlElement.CE_Header, option, painter, self)
        painter.restore()

        column_name = self.model().headerData(logical_index, self.orientation(), Qt.ItemDataRole.DisplayRole)
        if column_name is None:
            return

        content_rect = rect.adjusted(8, 3, -8, -3)
        badge_text = self.badge_text_for_section(logical_index)
        badge_font = self._badge_font()
        badge_metrics = QFontMetrics(badge_font)
        badge_width = badge_metrics.horizontalAdvance(badge_text) + 14
        badge_height = min(content_rect.height(), badge_metrics.height() + 8)
        badge_x = content_rect.right() - badge_width + 1
        badge_y = content_rect.center().y() - badge_height // 2
        badge_rect = QRect(badge_x, badge_y, badge_width, badge_height)
        text_rect = QRect(content_rect.left(), content_rect.top(), max(0, badge_rect.left() - content_rect.left() - 8), content_rect.height())

        painter.save()
        painter.setPen(QPen(self.palette().color(QPalette.ColorRole.WindowText)))
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            QFontMetrics(self.font()).elidedText(str(column_name), Qt.TextElideMode.ElideRight, text_rect.width()),
        )
        painter.restore()

        self._paint_badge(painter, badge_rect, badge_text)

    def mouseMoveEvent(self, event):
        logical_index = self.logicalIndexAt(event.position().toPoint())
        if logical_index >= 0:
            QToolTip.showText(event.globalPosition().toPoint(), self.section_tooltip_text(logical_index), self)
        else:
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        QToolTip.hideText()
        super().leaveEvent(event)

    def _badge_font(self):
        font = self.font()
        point_size = font.pointSize()
        if point_size <= 0:
            point_size = 9
        font.setPointSize(max(8, point_size - 1))
        font.setBold(True)
        return font

    def _paint_badge(self, painter, badge_rect: QRect, badge_text: str):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(self._badge_border_colour())))
        painter.setBrush(QColor(self._badge_background_colour()))
        painter.drawRoundedRect(badge_rect.adjusted(0, 0, -1, -1), 5, 5)
        painter.setFont(self._badge_font())
        painter.setPen(QPen(QColor(self._badge_text_colour())))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)
        painter.restore()

    def _badge_background_colour(self) -> str:
        if self._theme == "dark":
            return "#334155"
        if self._theme == "vivid":
            return "#e8eefc"
        return "#edf2f7"

    def _badge_border_colour(self) -> str:
        if self._theme == "dark":
            return "#4b5563"
        if self._theme == "vivid":
            return "#c2d1f4"
        return "#cbd5e1"

    def _badge_text_colour(self) -> str:
        if self._theme == "dark":
            return "#f8fafc"
        if self._theme == "vivid":
            return "#1e293b"
        return "#1f2937"


class ResultsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "light"
        self._null_colour = get_results_null_colour(self._theme)
        self._status_colours = get_results_status_colours(self._theme)

        # Raw data kept in sync with table display — export reads from here
        self._last_columns: list[str] = []
        self._last_rows: list[tuple] = []

        self._header = ResultsHeaderView(Qt.Orientation.Horizontal)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Status bar ──────────────────────────────────────────────────────
        status_bar = QWidget()
        status_bar.setFixedHeight(28)
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(6, 0, 6, 0)

        self.status_label = QLabel(RESULTS_STATUS_EMPTY)
        self.status_label.setStyleSheet("font-size: 12px;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        self.export_btn = QPushButton(RESULTS_EXPORT_BUTTON)
        self.export_btn.setFixedWidth(120)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._show_export_menu)
        status_layout.addWidget(self.export_btn)

        layout.addWidget(status_bar)

        # ── Results table ───────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setHorizontalHeader(self._header)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._header.setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.table)
        self.set_theme("light")

    def set_theme(self, theme: str):
        self._theme = (theme or "").strip().lower()
        self._null_colour = get_results_null_colour(self._theme)
        self._status_colours = get_results_status_colours(self._theme)
        self._header.set_theme(self._theme)

    # ── Public interface ────────────────────────────────────────────────────

    def show_results(self, columns: list, rows: list, elapsed: float, column_types: list[str] | None = None):
        self._last_columns = list(columns)
        self._last_rows = list(rows)
        if column_types is None:
            column_types = self._infer_column_types(rows, len(columns))
        self._header.set_column_types(column_types)
        self._populate_table(columns, rows)
        word = "row" if len(rows) == 1 else "rows"
        self._set_status(f"{len(rows)} {word}  ·  {elapsed * 1000:.1f} ms", "ok")
        self.export_btn.setEnabled(True)

    def show_error(self, error: str, elapsed: float):
        self._last_columns = []
        self._last_rows = []
        self._header.set_column_types([])
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self._set_status(f"Error  ·  {error}", "error")
        self.export_btn.setEnabled(False)

    def show_success_no_results(self, elapsed: float):
        self._last_columns = []
        self._last_rows = []
        self._header.set_column_types([])
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self._set_status(f"OK  ·  {elapsed * 1000:.1f} ms", "ok")
        self.export_btn.setEnabled(False)

    # ── Internals ───────────────────────────────────────────────────────────

    def _set_status(self, text: str, kind: str):
        colour = self._status_colours.get(kind, self._status_colours["neutral"])
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {colour}; font-size: 12px;")

    def _populate_table(self, columns: list, rows: list):
        self.table.setColumnCount(len(columns))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(columns)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                text = "NULL" if val is None else str(val)
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if val is None:
                    item.setForeground(QColor(self._null_colour))
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()

    def _infer_column_types(self, rows: list[tuple], column_count: int) -> list[str]:
        if column_count == 0:
            return []
        if not rows:
            return ["UNKNOWN"] * column_count

        column_types: list[str] = []
        for index in range(column_count):
            observed = [self._value_type_label(row[index]) for row in rows if row[index] is not None]
            if not observed:
                column_types.append("NULL")
                continue

            unique = set(observed)
            if len(unique) == 1:
                column_types.append(observed[0])
            elif unique <= {"INTEGER", "REAL", "NUMERIC"}:
                column_types.append("NUMERIC")
            elif unique <= {"DATE", "TIME", "TIMESTAMP"}:
                column_types.append("TEMPORAL")
            else:
                column_types.append("MIXED")
        return column_types

    def _value_type_label(self, value) -> str:
        if isinstance(value, bool):
            return "BOOLEAN"
        if isinstance(value, int):
            return "INTEGER"
        if isinstance(value, float):
            return "REAL"
        if isinstance(value, Decimal):
            return "NUMERIC"
        if isinstance(value, datetime):
            return "TIMESTAMP"
        if isinstance(value, date):
            return "DATE"
        if isinstance(value, time_type):
            return "TIME"
        if isinstance(value, (bytes, bytearray, memoryview)):
            return "BLOB"
        return "TEXT"

    def _type_tooltip_text(self, type_label: str) -> str:
        if type_label == "UNKNOWN":
            return "unknown (no rows to inspect)"
        if type_label == "NULL":
            return "NULL values only"
        if type_label == "MIXED":
            return "mixed values"
        if type_label == "NUMERIC":
            return "numeric values"
        if type_label == "TEMPORAL":
            return "temporal values"
        return type_label.lower()

    def _type_badge_icon(self, type_label: str) -> QIcon:
        text = {
            "BOOLEAN": "BOOL",
            "BLOB": "BLOB",
            "DATE": "DATE",
            "INTEGER": "INT",
            "MIXED": "MIX",
            "NULL": "NULL",
            "NUMERIC": "NUM",
            "REAL": "REAL",
            "TEMPORAL": "TIME",
            "TEXT": "TEXT",
            "TIME": "TIME",
            "TIMESTAMP": "TS",
            "UNKNOWN": "?",
        }.get(type_label, "?")

        pixmap = QPixmap(44, 18)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(self._null_colour))
        painter.setBrush(QColor(self._badge_background_colour()))
        painter.drawRoundedRect(pixmap.rect().adjusted(0, 0, -1, -1), 6, 6)

        font = QFont(painter.font())
        font.setBold(True)
        font.setPointSize(7)
        painter.setFont(font)
        painter.setPen(QColor(self._badge_text_colour()))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()

        return QIcon(pixmap)

    def _badge_background_colour(self) -> str:
        if self._theme == "dark":
            return "#2c3440"
        if self._theme == "vivid":
            return "#eef3ff"
        return "#eef2f6"

    def _badge_text_colour(self) -> str:
        if self._theme == "dark":
            return "#f5f7fa"
        if self._theme == "vivid":
            return "#1f2a44"
        return "#243242"

    def _show_export_menu(self):
        menu = QMenu(self)
        selected_csv_action = menu.addAction(RESULTS_EXPORT_SELECTED_CSV)
        selected_clipboard_action = menu.addAction(RESULTS_EXPORT_SELECTED_CLIPBOARD)
        all_csv_action = menu.addAction(RESULTS_EXPORT_ALL_CSV)
        all_clipboard_action = menu.addAction(RESULTS_EXPORT_ALL_CLIPBOARD)

        has_selection = self._has_selected_rows()
        selected_csv_action.setEnabled(has_selection)
        selected_clipboard_action.setEnabled(has_selection)

        chosen = menu.exec(
            self.export_btn.mapToGlobal(self.export_btn.rect().bottomLeft())
        )
        if chosen == selected_csv_action:
            self._export_csv(selected_only=True)
        elif chosen == selected_clipboard_action:
            self._copy_to_clipboard(selected_only=True)
        elif chosen == all_csv_action:
            self._export_csv(selected_only=False)
        elif chosen == all_clipboard_action:
            self._copy_to_clipboard(selected_only=False)

    def _export_csv(self, selected_only: bool = False):
        export_rows = self._rows_for_export(selected_only)
        if export_rows is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, RESULTS_EXPORT_DIALOG_TITLE, "", RESULTS_EXPORT_DIALOG_FILTER
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self._last_columns)
            writer.writerows(export_rows)

    def _copy_to_clipboard(self, selected_only: bool = False):
        export_rows = self._rows_for_export(selected_only)
        if export_rows is None:
            return

        def _format_cell(value):
            return "NULL" if value is None else str(value)

        lines = ["\t".join(self._last_columns)]
        lines.extend("\t".join(_format_cell(value) for value in row) for row in export_rows)
        QApplication.clipboard().setText("\n".join(lines))

    def _rows_for_export(self, selected_only: bool) -> list[tuple] | None:
        if not self._last_columns:
            return None

        if not selected_only:
            return list(self._last_rows)

        selected_rows = self._selected_row_indexes()
        return [self._last_rows[index] for index in selected_rows]

    def _has_selected_rows(self) -> bool:
        return bool(self._selected_row_indexes())

    def _selected_row_indexes(self) -> list[int]:
        selection_model = self.table.selectionModel()
        if selection_model is None:
            return []
        return sorted({index.row() for index in selection_model.selectedRows()})
