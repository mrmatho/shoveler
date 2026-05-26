import csv

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
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from .config.text import (
    RESULTS_EXPORT_BUTTON,
    RESULTS_EXPORT_CLIPBOARD,
    RESULTS_EXPORT_CSV,
    RESULTS_EXPORT_DIALOG_FILTER,
    RESULTS_EXPORT_DIALOG_TITLE,
    RESULTS_STATUS_EMPTY,
)
from .config.ui import get_results_null_colour, get_results_status_colours


class ResultsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "light"
        self._null_colour = get_results_null_colour(self._theme)
        self._status_colours = get_results_status_colours(self._theme)

        # Raw data kept in sync with table display — export reads from here
        self._last_columns: list[str] = []
        self._last_rows: list[tuple] = []

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
        self.export_btn.setFixedWidth(80)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._show_export_menu)
        status_layout.addWidget(self.export_btn)

        layout.addWidget(status_bar)

        # ── Results table ───────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.table)
        self.set_theme("light")

    def set_theme(self, theme: str):
        self._theme = (theme or "").strip().lower()
        self._null_colour = get_results_null_colour(self._theme)
        self._status_colours = get_results_status_colours(self._theme)

    # ── Public interface ────────────────────────────────────────────────────

    def show_results(self, columns: list, rows: list, elapsed: float):
        self._last_columns = list(columns)
        self._last_rows = list(rows)
        self._populate_table(columns, rows)
        word = "row" if len(rows) == 1 else "rows"
        self._set_status(f"{len(rows)} {word}  ·  {elapsed * 1000:.1f} ms", "ok")
        self.export_btn.setEnabled(True)

    def show_error(self, error: str, elapsed: float):
        self._last_columns = []
        self._last_rows = []
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self._set_status(f"Error  ·  {error}", "error")
        self.export_btn.setEnabled(False)

    def show_success_no_results(self, elapsed: float):
        self._last_columns = []
        self._last_rows = []
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

    def _show_export_menu(self):
        menu = QMenu(self)
        csv_action = menu.addAction(RESULTS_EXPORT_CSV)
        clipboard_action = menu.addAction(RESULTS_EXPORT_CLIPBOARD)
        chosen = menu.exec(
            self.export_btn.mapToGlobal(self.export_btn.rect().bottomLeft())
        )
        if chosen == csv_action:
            self._export_csv()
        elif chosen == clipboard_action:
            self._copy_to_clipboard()

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, RESULTS_EXPORT_DIALOG_TITLE, "", RESULTS_EXPORT_DIALOG_FILTER
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self._last_columns)
            writer.writerows(self._last_rows)

    def _copy_to_clipboard(self):
        if not self._last_columns:
            return

        def _format_cell(value):
            return "NULL" if value is None else str(value)

        lines = ["\t".join(self._last_columns)]
        lines.extend("\t".join(_format_cell(value) for value in row) for row in self._last_rows)
        QApplication.clipboard().setText("\n".join(lines))
