from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSplitter,
)
from PySide6.QtCore import Qt, Signal

from .editor import SqlEditor
from .results_panel import ResultsPanel


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

        self.run_btn = QPushButton("▶  Run")
        self.run_btn.setFixedWidth(90)
        self.run_btn.setToolTip("Run query (F5 or Ctrl+Enter)")
        self.run_btn.clicked.connect(self._on_run)
        toolbar_layout.addWidget(self.run_btn)
        toolbar_layout.addStretch()

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

    def show_result(self, result: dict):
        if result["error"]:
            self.results.show_error(result["error"], result["elapsed"])
        else:
            self.results.show_results(
                result["columns"], result["rows"], result["elapsed"]
            )

    def set_syntax_highlighting_enabled(self, enabled: bool):
        self.editor.set_syntax_highlighting_enabled(enabled)
