import os

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from .editor import SqlEditor
from .results_panel import ResultsPanel
from .config.text import (
    QUERYTAB_EXPORT_DEFAULT_NAME,
    QUERYTAB_EXPORT_DIALOG_FILTER,
    QUERYTAB_EXPORT_DIALOG_TITLE,
    QUERYTAB_EXPORT_EMPTY_MESSAGE,
    QUERYTAB_EXPORT_EMPTY_TITLE,
    QUERYTAB_EXPORT_FAILED,
    QUERYTAB_EXPORT_SQL,
    QUERYTAB_EXPORT_SQL_TOOLTIP,
    QUERYTAB_LOAD_DIALOG_FILTER,
    QUERYTAB_LOAD_DIALOG_TITLE,
    QUERYTAB_LOAD_FAILED,
    QUERYTAB_LOAD_SQL,
    QUERYTAB_LOAD_SQL_TOOLTIP,
    QUERYTAB_RUN_QUERY,
    QUERYTAB_RUN_TOOLTIP,
)


class QueryTab(QWidget):
    run_requested = Signal(str)  # emits SQL string to main window

    def __init__(self, parent=None, syntax_highlighting_enabled: bool = True):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ── Run toolbar ─────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.addStretch()

        self.load_sql_btn = QPushButton(QUERYTAB_LOAD_SQL)
        self.load_sql_btn.setFixedWidth(90)
        self.load_sql_btn.setToolTip(QUERYTAB_LOAD_SQL_TOOLTIP)
        self.load_sql_btn.clicked.connect(self._load_sql)
        toolbar_layout.addWidget(self.load_sql_btn)

        self.export_sql_btn = QPushButton(QUERYTAB_EXPORT_SQL)
        self.export_sql_btn.setFixedWidth(95)
        self.export_sql_btn.setToolTip(QUERYTAB_EXPORT_SQL_TOOLTIP)
        self.export_sql_btn.clicked.connect(self._export_sql)
        toolbar_layout.addWidget(self.export_sql_btn)

        self.run_btn = QPushButton(QUERYTAB_RUN_QUERY)
        self.run_btn.setFixedWidth(120)
        self.run_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2e8b57;
                color: white;
                border: 1px solid #256f46;
                border-radius: 4px;
                font-weight: 600;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #257046;
            }
            QPushButton:pressed {
                background-color: #1f5f3b;
            }
            QPushButton:disabled {
                background-color: #6e8f7d;
                color: #e6e6e6;
            }
            """
        )
        self.run_btn.setToolTip(QUERYTAB_RUN_TOOLTIP)
        self.run_btn.clicked.connect(self._on_run)
        toolbar_layout.addWidget(self.run_btn)

        layout.addWidget(toolbar)

        # ── Editor / results splitter ────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Vertical)

        self.editor = SqlEditor()
        self.editor.set_syntax_highlighting_enabled(syntax_highlighting_enabled)
        self.editor.run_requested.connect(self._on_run)
        splitter.addWidget(self.editor)

        self.results = ResultsPanel()
        splitter.addWidget(self.results)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([250, 350])

        layout.addWidget(splitter)

    def _on_run(self):
        sql = self.editor.get_sql()
        if sql:
            self.run_requested.emit(sql)

    def _load_sql(self):
        self.open_sql_file_dialog()

    def open_sql_file_dialog(self) -> bool:
        path, _ = QFileDialog.getOpenFileName(
            self,
            QUERYTAB_LOAD_DIALOG_TITLE,
            "",
            QUERYTAB_LOAD_DIALOG_FILTER,
        )
        if not path:
            return False

        return self._load_sql_from_path(path)

    def _load_sql_from_path(self, path: str) -> bool:
        try:
            with open(path, "r", encoding="utf-8") as f:
                sql = f.read()
        except Exception as e:
            QMessageBox.critical(self, QUERYTAB_LOAD_FAILED, str(e))
            return False

        self.editor.setPlainText(sql)
        self.editor.setFocus()
        return True

    def _export_sql(self):
        sql = self.editor.toPlainText()
        if not sql.strip():
            QMessageBox.information(self, QUERYTAB_EXPORT_EMPTY_TITLE, QUERYTAB_EXPORT_EMPTY_MESSAGE)
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            QUERYTAB_EXPORT_DIALOG_TITLE,
            QUERYTAB_EXPORT_DEFAULT_NAME,
            QUERYTAB_EXPORT_DIALOG_FILTER,
        )
        if not path:
            return

        if not os.path.splitext(path)[1]:
            path += ".sql"

        try:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(sql)
        except Exception as e:
            QMessageBox.critical(self, QUERYTAB_EXPORT_FAILED, str(e))

    def show_result(self, result: dict):
        if result["error"]:
            self.results.show_error(result["error"], result["elapsed"])
        else:
            self.results.show_results(
                result["columns"], result["rows"], result["elapsed"]
            )

    def set_syntax_highlighting_enabled(self, enabled: bool):
        self.editor.set_syntax_highlighting_enabled(enabled)

    def set_theme(self, theme: str):
        self.editor.set_theme(theme)
        self.results.set_theme(theme)
