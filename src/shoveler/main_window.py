from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QTabWidget,
    QPushButton,
    QMessageBox,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import QSettings, Qt

from .db import Database
from .db_status_widget import DatabaseStatusWidget
from .schema_panel import SchemaPanel
from .query_tab import QueryTab


class MainWindow(QMainWindow):
    _SYNTAX_HIGHLIGHTING_KEY = "editor/syntax_highlighting_enabled"

    def __init__(self):
        super().__init__()
        self.db = Database()
        self.settings = QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "mrmatho",
            "shoveler",
        )
        self.syntax_highlighting_enabled = self._read_bool_setting(
            self._SYNTAX_HIGHLIGHTING_KEY, True
        )
        self.setWindowTitle("Shoveler: DuckDB Workbench")
        self.resize(1200, 720)

        self._build_ui()
        self._build_menu()
        self._connect_signals()

    # ── UI construction ─────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Status widget spans full width at the top
        self.db_status = DatabaseStatusWidget()
        root.addWidget(self.db_status)

        # Horizontal splitter: schema panel | query area
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.schema_panel = SchemaPanel()
        self.schema_panel.setMinimumWidth(160)
        self.schema_panel.setMaximumWidth(360)
        splitter.addWidget(self.schema_panel)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)

        # "+" button in the tab bar corner
        add_tab_btn = QPushButton("+")
        add_tab_btn.setFixedSize(26, 26)
        add_tab_btn.setToolTip("New query tab")
        add_tab_btn.clicked.connect(self._add_tab)
        self.tab_widget.setCornerWidget(add_tab_btn, Qt.Corner.TopRightCorner)

        splitter.addWidget(self.tab_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 980])

        root.addWidget(splitter)

        # Qt status bar for transient messages
        self.statusBar().showMessage("Ready")

        # Start with one blank query tab
        self._add_tab()

    def _build_menu(self):
        view_menu = self.menuBar().addMenu("&View")

        self.syntax_highlighting_action = QAction("Syntax highlighting", self)
        self.syntax_highlighting_action.setCheckable(True)
        self.syntax_highlighting_action.setChecked(self.syntax_highlighting_enabled)
        self.syntax_highlighting_action.toggled.connect(
            self._set_syntax_highlighting_enabled
        )
        view_menu.addAction(self.syntax_highlighting_action)

    def _connect_signals(self):
        self.db_status.file_opened.connect(self._open_file)
        self.db_status.memory_requested.connect(self._new_memory)
        self.db_status.checkpoint_requested.connect(self._checkpoint)
        self.schema_panel.table_double_clicked.connect(self._insert_table_name)

    def _read_bool_setting(self, key: str, default: bool) -> bool:
        value = self.settings.value(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        return bool(value)

    def _set_syntax_highlighting_enabled(self, enabled: bool):
        self.syntax_highlighting_enabled = bool(enabled)
        self.settings.setValue(
            self._SYNTAX_HIGHLIGHTING_KEY,
            self.syntax_highlighting_enabled,
        )
        self.settings.sync()
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            if isinstance(tab, QueryTab):
                tab.set_syntax_highlighting_enabled(self.syntax_highlighting_enabled)
        state = "enabled" if self.syntax_highlighting_enabled else "disabled"
        self.statusBar().showMessage(f"Syntax highlighting {state}", 2000)

    # ── Tab management ──────────────────────────────────────────────────────

    def _add_tab(self) -> QueryTab:
        n = self.tab_widget.count() + 1
        tab = QueryTab(syntax_highlighting_enabled=self.syntax_highlighting_enabled)
        tab.run_requested.connect(self._run_query)
        idx = self.tab_widget.addTab(tab, f"Query {n}")
        self.tab_widget.setCurrentIndex(idx)
        return tab

    def _close_tab(self, index: int):
        if self.tab_widget.count() == 1:
            # Always keep at least one tab; just clear its contents
            tab: QueryTab = self.tab_widget.widget(0)
            tab.editor.clear()
            return
        self.tab_widget.removeTab(index)

    def _current_tab(self) -> QueryTab | None:
        return self.tab_widget.currentWidget()

    # ── Query execution ─────────────────────────────────────────────────────

    def _run_query(self, sql: str):
        result = self.db.execute(sql)
        tab = self._current_tab()
        if tab:
            tab.show_result(result)
        # Refresh schema — query may have created/dropped tables
        if self.db.is_connected:
            self.schema_panel.refresh(self.db)
        if result["error"]:
            self.statusBar().showMessage(f"Error: {result['error']}", 5000)
        else:
            rows = len(result["rows"])
            word = "row" if rows == 1 else "rows"
            self.statusBar().showMessage(
                f"{rows} {word}  ·  {result['elapsed'] * 1000:.1f} ms", 4000
            )

    # ── Database actions ────────────────────────────────────────────────────

    def _open_file(self, path: str):
        try:
            self.db.open_file(path)
            self.db_status.set_file_mode(path)
            self.schema_panel.refresh(self.db)
            self.setWindowTitle(f"DuckDB Workbench — {path}")
            self.statusBar().showMessage(f"Opened {path}", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Could not open file", str(e))

    def _new_memory(self):
        self.db.new_memory()
        self.db_status.set_memory_mode()
        self.schema_panel.refresh(self.db)
        self.setWindowTitle("DuckDB Workbench — In-Memory")
        self.statusBar().showMessage("In-memory database created", 4000)

    def _checkpoint(self):
        try:
            self.db.checkpoint()
            self.db_status.notify_checkpoint_ok()
            self.statusBar().showMessage("Checkpoint complete", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Checkpoint failed", str(e))

    def _insert_table_name(self, table_name: str):
        tab = self._current_tab()
        if tab:
            tab.editor.insertPlainText(table_name)
            tab.editor.setFocus()

    # ── Cleanup ─────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self.db.close()
        event.accept()
