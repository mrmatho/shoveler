import os

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QTabWidget,
    QPushButton,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtCore import QSettings, Qt

from .db import Database
from .db_status_widget import DatabaseStatusWidget
from .schema_panel import SchemaPanel
from .query_tab import QueryTab


class MainWindow(QMainWindow):
    _SYNTAX_HIGHLIGHTING_KEY = "editor/syntax_highlighting_enabled"
    _THEME_KEY = "ui/theme"
    _LIGHT_THEME_STYLESHEET = """
    QMainWindow {
        background-color: #f4f7fb;
    }

    QWidget {
        color: #1f2937;
    }

    QMenuBar {
        background-color: #f4f7fb;
        border-bottom: 1px solid #d7deea;
    }

    QMenuBar::item {
        background: transparent;
        padding: 4px 8px;
    }

    QMenuBar::item:selected {
        background-color: #eaf0f8;
        border-radius: 4px;
    }

    QMenu {
        background-color: #ffffff;
        border: 1px solid #d7deea;
    }

    QMenu::item:selected {
        background-color: #eaf0f8;
    }

    QStatusBar {
        background-color: #eef3f9;
        border-top: 1px solid #d7deea;
    }

    QDialog,
    QMessageBox,
    QInputDialog {
        background-color: #f7faff;
        color: #1f2937;
    }

    QToolTip {
        background-color: #ffffff;
        color: #1f2937;
        border: 1px solid #d7deea;
        padding: 4px;
    }

    QPlainTextEdit,
    QTableWidget,
    QTreeWidget,
    QListWidget,
    QLineEdit {
        background-color: #ffffff;
        border: 1px solid #d7deea;
        border-radius: 4px;
        selection-background-color: #d8e7fb;
    }

    QAbstractItemView {
        background-color: #ffffff;
        alternate-background-color: #f4f8ff;
        color: #1f2937;
        gridline-color: #d7deea;
        selection-background-color: #d8e7fb;
        selection-color: #1f2937;
    }

    QHeaderView::section {
        background-color: #edf3fb;
        color: #475569;
        border: 1px solid #d7deea;
        padding: 2px 4px;
    }

    QTableCornerButton::section {
        background-color: #edf3fb;
        border: 1px solid #d7deea;
    }

    QTabWidget::pane {
        border: 1px solid #d7deea;
        background-color: #f8fbff;
    }

    QTabBar::tab {
        background-color: #eaf0f8;
        border: 1px solid #d7deea;
        border-bottom: none;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        padding: 5px 10px;
        margin-right: 2px;
    }

    QTabBar::tab:selected {
        background-color: #ffffff;
    }

    QPushButton {
        background-color: #f9fbff;
        border: 1px solid #ccd6e3;
        border-radius: 5px;
        padding: 4px 10px;
    }

    QPushButton:hover {
        background-color: #edf3fb;
    }

    QPushButton:pressed {
        background-color: #e2ebf7;
    }

    QPushButton:disabled {
        color: #8a96a8;
        background-color: #f1f4f9;
        border-color: #d7deea;
    }

    QSplitter::handle {
        background-color: #dfe6f1;
    }

    QSplitter::handle:hover {
        background-color: #c8d5e8;
    }
    """
    _DARK_THEME_STYLESHEET = """
    QMainWindow {
        background-color: #1e2430;
    }

    QWidget {
        color: #d9e2ef;
    }

    QMenuBar {
        background-color: #1e2430;
        border-bottom: 1px solid #384457;
    }

    QMenuBar::item {
        background: transparent;
        padding: 4px 8px;
    }

    QMenuBar::item:selected {
        background-color: #2b3545;
        border-radius: 4px;
    }

    QMenu {
        background-color: #252d3a;
        border: 1px solid #3b4659;
    }

    QMenu::item:selected {
        background-color: #334156;
    }

    QStatusBar {
        background-color: #202938;
        border-top: 1px solid #384457;
    }

    QDialog,
    QMessageBox,
    QInputDialog {
        background-color: #252d3a;
        color: #d9e2ef;
    }

    QToolTip {
        background-color: #2b3545;
        color: #d9e2ef;
        border: 1px solid #46556d;
        padding: 4px;
    }

    QPlainTextEdit,
    QTableWidget,
    QTreeWidget,
    QListWidget,
    QLineEdit {
        background-color: #1f2734;
        border: 1px solid #3b4659;
        border-radius: 4px;
        selection-background-color: #38506f;
    }

    QAbstractItemView {
        background-color: #1f2734;
        alternate-background-color: #232d3d;
        color: #d9e2ef;
        gridline-color: #303d51;
        selection-background-color: #38506f;
        selection-color: #f2f6fc;
    }

    QHeaderView::section {
        background-color: #273143;
        color: #c7d2e3;
        border: 1px solid #3b4659;
        padding: 2px 4px;
    }

    QTableCornerButton::section {
        background-color: #273143;
        border: 1px solid #3b4659;
    }

    QTabWidget::pane {
        border: 1px solid #3b4659;
        background-color: #232c3b;
    }

    QTabBar::tab {
        background-color: #2b3545;
        border: 1px solid #3b4659;
        border-bottom: none;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        padding: 5px 10px;
        margin-right: 2px;
    }

    QTabBar::tab:selected {
        background-color: #1f2734;
    }

    QPushButton {
        background-color: #2b3647;
        border: 1px solid #46556d;
        border-radius: 5px;
        padding: 4px 10px;
    }

    QPushButton:hover {
        background-color: #334156;
    }

    QPushButton:pressed {
        background-color: #3a4a63;
    }

    QPushButton:disabled {
        color: #8594aa;
        background-color: #252d3a;
        border-color: #3b4659;
    }

    QSplitter::handle {
        background-color: #3b4659;
    }

    QSplitter::handle:hover {
        background-color: #4a5a72;
    }
    """

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
        self.theme = self._read_theme_setting()
        self.setWindowTitle("Shoveler: Duck DB Workbench")
        self.resize(1200, 720)

        self._build_ui()
        self._build_menu()
        self._set_theme(self.theme, persist=False, show_message=False)
        self._connect_signals()
        self._new_memory()

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
        splitter.setSizes([260, 940])

        root.addWidget(splitter)

        # Qt status bar for transient messages
        self.statusBar().showMessage("Ready")

        # Start with one blank query tab
        self._add_tab()

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("&File")

        self.open_sql_action = QAction("Open SQL...", self)
        self.open_sql_action.setShortcut("Ctrl+O")
        self.open_sql_action.triggered.connect(self._open_sql_file)
        file_menu.addAction(self.open_sql_action)

        self.save_as_action = QAction("Save Database As...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.setEnabled(False)
        self.save_as_action.triggered.connect(self._save_database_as)
        file_menu.addAction(self.save_as_action)

        view_menu = self.menuBar().addMenu("&View")

        self.syntax_highlighting_action = QAction("Syntax highlighting", self)
        self.syntax_highlighting_action.setCheckable(True)
        self.syntax_highlighting_action.setChecked(self.syntax_highlighting_enabled)
        self.syntax_highlighting_action.toggled.connect(
            self._set_syntax_highlighting_enabled
        )
        view_menu.addAction(self.syntax_highlighting_action)

        theme_menu = view_menu.addMenu("Theme")
        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setExclusive(True)

        self.light_theme_action = QAction("Light", self)
        self.light_theme_action.setCheckable(True)
        self.light_theme_action.triggered.connect(lambda: self._set_theme("light"))
        theme_menu.addAction(self.light_theme_action)
        self.theme_action_group.addAction(self.light_theme_action)

        self.dark_theme_action = QAction("Dark", self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.triggered.connect(lambda: self._set_theme("dark"))
        theme_menu.addAction(self.dark_theme_action)
        self.theme_action_group.addAction(self.dark_theme_action)

        self.light_theme_action.setChecked(self.theme == "light")
        self.dark_theme_action.setChecked(self.theme == "dark")

    def _connect_signals(self):
        self.db_status.file_opened.connect(self._open_file)
        self.db_status.memory_requested.connect(self._new_memory)
        self.db_status.save_requested.connect(self._save_database_as)
        self.db_status.checkpoint_requested.connect(self._checkpoint)
        self.schema_panel.table_double_clicked.connect(self._insert_table_name)
        self.schema_panel.working_directory_changed.connect(
            self._on_working_directory_changed
        )

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

    def _read_theme_setting(self) -> str:
        value = self.settings.value(self._THEME_KEY, "light")
        if isinstance(value, str) and value.strip().lower() in {"light", "dark"}:
            return value.strip().lower()
        return "light"

    def _set_theme(self, theme: str, persist: bool = True, show_message: bool = True):
        normalized = (theme or "").strip().lower()
        if normalized not in {"light", "dark"}:
            normalized = "light"

        if normalized == "dark":
            self.setStyleSheet(self._DARK_THEME_STYLESHEET)
            self.dark_theme_action.setChecked(True)
        else:
            self.setStyleSheet(self._LIGHT_THEME_STYLESHEET)
            self.light_theme_action.setChecked(True)

        self.theme = normalized
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            if isinstance(tab, QueryTab):
                tab.set_theme(self.theme)

        if persist:
            self.settings.setValue(self._THEME_KEY, self.theme)
            self.settings.sync()

        if show_message:
            self.statusBar().showMessage(f"Theme set to {self.theme}", 2000)

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
        tab.set_theme(self.theme)
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

    def _open_sql_file(self):
        tab = self._current_tab()
        if not tab:
            return

        if tab.open_sql_file_dialog():
            self.statusBar().showMessage("SQL file loaded", 3000)

    def _open_file(self, path: str):
        try:
            self.db.open_file(path)
            self.db_status.set_file_mode(path)
            self.schema_panel.refresh(self.db)
            self.setWindowTitle(f"Shoveler: Duck DB Workbench — {path}")
            self.save_as_action.setEnabled(True)
            self.statusBar().showMessage(f"Opened {path}", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Could not open file", str(e))

    def _new_memory(self):
        if self._should_confirm_close_in_memory():
            choice = self._confirm_close_in_memory()
            if choice == QMessageBox.StandardButton.Cancel:
                return
            if choice == QMessageBox.StandardButton.Save and not self._save_database_as():
                return

        self.db.new_memory()
        self.db_status.set_memory_mode()
        self.schema_panel.refresh(self.db)
        self.setWindowTitle("Shoveler: Duck DB Workbench — In-Memory")
        self.save_as_action.setEnabled(True)
        self.statusBar().showMessage("In-memory database created", 4000)

    def _save_database_as(self) -> bool:
        if not self.db.is_connected:
            QMessageBox.information(self, "Nothing to save", "No database connected.")
            return False

        default_path = self.db.path or ""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save DuckDB Database As",
            default_path,
            "DuckDB Files (*.duckdb *.db);;All Files (*)",
        )
        if not path:
            return False

        if not os.path.splitext(path)[1]:
            path += ".duckdb"

        try:
            saved_path = self.db.save_as(path)
            self.db_status.set_file_mode(saved_path)
            self.schema_panel.refresh(self.db)
            self.setWindowTitle(f"Shoveler: Duck DB Workbench — {saved_path}")
            self.statusBar().showMessage(f"Saved database to {saved_path}", 4000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))
            return False

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

    def _on_working_directory_changed(self, path: str):
        self.statusBar().showMessage(f"Working directory set to {path}", 4000)

    def _confirm_close_in_memory(self) -> QMessageBox.StandardButton:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Unsaved In-Memory Database")
        box.setText("You are using an in-memory database.")
        box.setInformativeText(
            "Data will be lost when the app closes. Save the database before closing?"
        )
        box.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )
        box.setDefaultButton(QMessageBox.StandardButton.Save)
        box.setButtonText(QMessageBox.StandardButton.Save, "Save Database As...")
        return QMessageBox.StandardButton(box.exec())

    def _should_confirm_close_in_memory(self) -> bool:
        if not self.db.is_connected or self.db.mode != "memory":
            return False
        return len(self.db.get_tables()) > 0

    # ── Cleanup ─────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._should_confirm_close_in_memory():
            choice = self._confirm_close_in_memory()
            if choice == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if choice == QMessageBox.StandardButton.Save and not self._save_database_as():
                event.ignore()
                return

        self.db.close()
        event.accept()
