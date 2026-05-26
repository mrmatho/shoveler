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
from .config.text import (
    ACTION_OPEN_SQL,
    ACTION_SAVE_DATABASE_AS,
    ACTION_SYNTAX_HIGHLIGHTING,
    ACTION_THEME_DARK,
    ACTION_THEME_LIGHT,
    ACTION_THEME_VIVID,
    CHECKPOINT_FAILED_TITLE,
    MENU_FILE,
    MENU_THEME,
    MENU_VIEW,
    NEW_TAB_BUTTON_LABEL,
    NEW_TAB_BUTTON_TOOLTIP,
    OPEN_FILE_ERROR_TITLE,
    SAVE_DIALOG_FILTER,
    SAVE_DIALOG_TITLE,
    SAVE_FAILED_TITLE,
    SAVE_NOTHING_MESSAGE,
    SAVE_NOTHING_TITLE,
    STATUS_READY,
    STATUS_CHECKPOINT_COMPLETE,
    STATUS_IN_MEMORY_CREATED,
    STATUS_SQL_FILE_LOADED,
    UNSAVED_MEMORY_INFO,
    UNSAVED_MEMORY_TEXT,
    UNSAVED_MEMORY_TITLE,
    WINDOW_TITLE_BASE,
    status_opened,
    status_query_error,
    status_query_ok,
    status_saved,
    status_syntax_highlighting,
    status_theme_set,
    status_working_directory_set,
    tab_title,
    window_title_in_memory,
    window_title_with_path,
)
from .config.theme import DEFAULT_THEME, load_theme_stylesheet, normalize_theme


class MainWindow(QMainWindow):
    _SYNTAX_HIGHLIGHTING_KEY = "editor/syntax_highlighting_enabled"
    _THEME_KEY = "ui/theme"
    _WORKING_DIRECTORY_KEY = "files/working_directory"

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
        self.setWindowTitle(WINDOW_TITLE_BASE)
        self.resize(1200, 720)

        self._build_ui()
        self._build_menu()
        self._set_theme(self.theme, persist=False, show_message=False)
        self._connect_signals()
        self._restore_working_directory()
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
        add_tab_btn = QPushButton(NEW_TAB_BUTTON_LABEL)
        add_tab_btn.setFixedSize(26, 26)
        add_tab_btn.setToolTip(NEW_TAB_BUTTON_TOOLTIP)
        add_tab_btn.clicked.connect(self._add_tab)
        self.tab_widget.setCornerWidget(add_tab_btn, Qt.Corner.TopRightCorner)

        splitter.addWidget(self.tab_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 940])

        root.addWidget(splitter)

        # Qt status bar for transient messages
        self.statusBar().showMessage(STATUS_READY)

        # Start with one blank query tab
        self._add_tab()

    def _build_menu(self):
        file_menu = self.menuBar().addMenu(MENU_FILE)

        self.open_sql_action = QAction(ACTION_OPEN_SQL, self)
        self.open_sql_action.setShortcut("Ctrl+O")
        self.open_sql_action.triggered.connect(self._open_sql_file)
        file_menu.addAction(self.open_sql_action)

        self.save_as_action = QAction(ACTION_SAVE_DATABASE_AS, self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.setEnabled(False)
        self.save_as_action.triggered.connect(self._save_database_as)
        file_menu.addAction(self.save_as_action)

        view_menu = self.menuBar().addMenu(MENU_VIEW)

        self.syntax_highlighting_action = QAction(ACTION_SYNTAX_HIGHLIGHTING, self)
        self.syntax_highlighting_action.setCheckable(True)
        self.syntax_highlighting_action.setChecked(self.syntax_highlighting_enabled)
        self.syntax_highlighting_action.toggled.connect(
            self._set_syntax_highlighting_enabled
        )
        view_menu.addAction(self.syntax_highlighting_action)

        theme_menu = view_menu.addMenu(MENU_THEME)
        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setExclusive(True)

        self.light_theme_action = QAction(ACTION_THEME_LIGHT, self)
        self.light_theme_action.setCheckable(True)
        self.light_theme_action.triggered.connect(lambda: self._set_theme("light"))
        theme_menu.addAction(self.light_theme_action)
        self.theme_action_group.addAction(self.light_theme_action)

        self.dark_theme_action = QAction(ACTION_THEME_DARK, self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.triggered.connect(lambda: self._set_theme("dark"))
        theme_menu.addAction(self.dark_theme_action)
        self.theme_action_group.addAction(self.dark_theme_action)

        self.vivid_theme_action = QAction(ACTION_THEME_VIVID, self)
        self.vivid_theme_action.setCheckable(True)
        self.vivid_theme_action.triggered.connect(lambda: self._set_theme("vivid"))
        theme_menu.addAction(self.vivid_theme_action)
        self.theme_action_group.addAction(self.vivid_theme_action)

        self.light_theme_action.setChecked(self.theme == "light")
        self.dark_theme_action.setChecked(self.theme == "dark")
        self.vivid_theme_action.setChecked(self.theme == "vivid")

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
        if isinstance(value, str):
            return normalize_theme(value)
        return DEFAULT_THEME

    def _set_theme(self, theme: str, persist: bool = True, show_message: bool = True):
        normalized = normalize_theme(theme)
        self.setStyleSheet(load_theme_stylesheet(normalized))

        if normalized == "dark":
            self.dark_theme_action.setChecked(True)
        elif normalized == "vivid":
            self.vivid_theme_action.setChecked(True)
        else:
            self.light_theme_action.setChecked(True)

        self.theme = normalized
        self.db_status.set_theme(self.theme)
        self.schema_panel.set_theme(self.theme)
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            if isinstance(tab, QueryTab):
                tab.set_theme(self.theme)

        if persist:
            self.settings.setValue(self._THEME_KEY, self.theme)
            self.settings.sync()

        if show_message:
            self.statusBar().showMessage(status_theme_set(self.theme), 2000)

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
        self.statusBar().showMessage(status_syntax_highlighting(state), 2000)

    # ── Tab management ──────────────────────────────────────────────────────

    def _add_tab(self) -> QueryTab:
        n = self.tab_widget.count() + 1
        tab = QueryTab(syntax_highlighting_enabled=self.syntax_highlighting_enabled)
        tab.set_theme(self.theme)
        tab.run_requested.connect(self._run_query)
        idx = self.tab_widget.addTab(tab, tab_title(n))
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
            self.statusBar().showMessage(status_query_error(result["error"]), 5000)
        else:
            rows = len(result["rows"])
            self.statusBar().showMessage(status_query_ok(rows, result["elapsed"]), 4000)

    # ── Database actions ────────────────────────────────────────────────────

    def _open_sql_file(self):
        tab = self._current_tab()
        if not tab:
            return

        if tab.open_sql_file_dialog():
            self.statusBar().showMessage(STATUS_SQL_FILE_LOADED, 3000)

    def _open_file(self, path: str):
        try:
            self.db.open_file(path)
            self.db_status.set_file_mode(path)
            self.schema_panel.refresh(self.db)
            self.setWindowTitle(window_title_with_path(path))
            self.save_as_action.setEnabled(True)
            self.statusBar().showMessage(status_opened(path), 4000)
        except Exception as e:
            QMessageBox.critical(self, OPEN_FILE_ERROR_TITLE, str(e))

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
        self.setWindowTitle(window_title_in_memory())
        self.save_as_action.setEnabled(True)
        self.statusBar().showMessage(STATUS_IN_MEMORY_CREATED, 4000)

    def _save_database_as(self) -> bool:
        if not self.db.is_connected:
            QMessageBox.information(self, SAVE_NOTHING_TITLE, SAVE_NOTHING_MESSAGE)
            return False

        default_path = self.db.path or ""
        path, _ = QFileDialog.getSaveFileName(
            self,
            SAVE_DIALOG_TITLE,
            default_path,
            SAVE_DIALOG_FILTER,
        )
        if not path:
            return False

        if not os.path.splitext(path)[1]:
            path += ".duckdb"

        try:
            saved_path = self.db.save_as(path)
            self.db_status.set_file_mode(saved_path)
            self.schema_panel.refresh(self.db)
            self.setWindowTitle(window_title_with_path(saved_path))
            self.statusBar().showMessage(status_saved(saved_path), 4000)
            return True
        except Exception as e:
            QMessageBox.critical(self, SAVE_FAILED_TITLE, str(e))
            return False

    def _checkpoint(self):
        try:
            self.db.checkpoint()
            self.db_status.notify_checkpoint_ok()
            self.statusBar().showMessage(STATUS_CHECKPOINT_COMPLETE, 3000)
        except Exception as e:
            QMessageBox.critical(self, CHECKPOINT_FAILED_TITLE, str(e))

    def _insert_table_name(self, table_name: str):
        tab = self._current_tab()
        if tab:
            tab.editor.insertPlainText(table_name)
            tab.editor.setFocus()

    def _on_working_directory_changed(self, path: str):
        self.settings.setValue(self._WORKING_DIRECTORY_KEY, path)
        self.settings.sync()
        self.statusBar().showMessage(status_working_directory_set(path), 4000)

    def _restore_working_directory(self):
        saved = self.settings.value(self._WORKING_DIRECTORY_KEY, "")
        saved_path = saved.strip() if isinstance(saved, str) else ""
        home_dir = os.path.expanduser("~")
        documents_dir = os.path.join(home_dir, "Documents")
        default_dir = documents_dir if os.path.isdir(documents_dir) else home_dir
        target_dir = saved_path if saved_path and os.path.isdir(saved_path) else default_dir

        try:
            os.chdir(target_dir)
        except Exception:
            return

        self.schema_panel.refresh_working_directory()

    def _confirm_close_in_memory(self) -> QMessageBox.StandardButton:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(UNSAVED_MEMORY_TITLE)
        box.setText(UNSAVED_MEMORY_TEXT)
        box.setInformativeText(UNSAVED_MEMORY_INFO)
        box.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )
        box.setDefaultButton(QMessageBox.StandardButton.Save)
        box.setButtonText(QMessageBox.StandardButton.Save, ACTION_SAVE_DATABASE_AS)
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
