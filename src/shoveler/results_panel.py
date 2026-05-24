import csv

from PySide6.QtWidgets import (
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


class ResultsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

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

        self.status_label = QLabel("No results yet")
        self.status_label.setStyleSheet("color: #888; font-size: 12px;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        self.export_btn = QPushButton("Export ▾")
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
        colours = {"ok": "#2a9d2a", "error": "#cc2200", "neutral": "#888"}
        colour = colours.get(kind, "#888")
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
                    item.setForeground(QColor("#aaaaaa"))
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()

    def _show_export_menu(self):
        menu = QMenu(self)
        csv_action = menu.addAction("Export as CSV…")
        chosen = menu.exec(
            self.export_btn.mapToGlobal(self.export_btn.rect().bottomLeft())
        )
        if chosen == csv_action:
            self._export_csv()

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export as CSV", "", "CSV Files (*.csv)"
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self._last_columns)
            writer.writerows(self._last_rows)
