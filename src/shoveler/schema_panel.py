import os

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QLineEdit,
    QPushButton,
    QListWidget,
    QSplitter,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor


class SchemaPanel(QWidget):
    table_double_clicked = Signal(str)
    working_directory_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(4)

        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        schema_widget = QWidget()
        schema_layout = QVBoxLayout(schema_widget)
        schema_layout.setContentsMargins(0, 0, 0, 0)
        schema_layout.setSpacing(4)

        heading = QLabel("Schema")
        heading.setStyleSheet("font-weight: bold; font-size: 12px; color: #555;")
        schema_layout.addWidget(heading)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Name", "Type"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setStyleSheet("font-size: 12px;")
        self.tree.header().setDefaultSectionSize(100)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        schema_layout.addWidget(self.tree)

        self._empty_label = QLabel("Open a database\nto see its tables.")
        self._empty_label.setStyleSheet("color: #aaa; font-size: 11px; padding: 8px;")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        schema_layout.addWidget(self._empty_label)

        files_widget = QWidget()
        files_layout = QVBoxLayout(files_widget)
        files_layout.setContentsMargins(0, 0, 0, 0)
        files_layout.setSpacing(4)

        files_heading = QLabel("Working Directory Files")
        files_heading.setStyleSheet("font-weight: bold; font-size: 12px; color: #555;")
        files_layout.addWidget(files_heading)

        path_row = QHBoxLayout()
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.setSpacing(4)

        self.cwd_path = QLineEdit()
        self.cwd_path.setReadOnly(True)
        self.cwd_path.setPlaceholderText("Current working directory")
        path_row.addWidget(self.cwd_path)

        self.change_dir_btn = QPushButton("Change...")
        self.change_dir_btn.setToolTip("Choose a working directory")
        self.change_dir_btn.clicked.connect(self._choose_working_directory)
        path_row.addWidget(self.change_dir_btn)

        files_layout.addLayout(path_row)

        self.files_list = QListWidget()
        self.files_list.setAlternatingRowColors(True)
        self.files_list.setStyleSheet("font-size: 12px;")
        files_layout.addWidget(self.files_list)

        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 0, 0, 0)
        footer_row.setSpacing(4)
        footer_row.addStretch()

        self.refresh_files_btn = QPushButton("Refresh")
        self.refresh_files_btn.clicked.connect(self.refresh_working_directory)
        footer_row.addWidget(self.refresh_files_btn)

        files_layout.addLayout(footer_row)

        splitter.addWidget(schema_widget)
        splitter.addWidget(files_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([320, 180])

        self._show_empty(True)
        self.refresh_working_directory()

    def refresh_working_directory(self):
        cwd = os.getcwd()
        self.cwd_path.setText(cwd)
        self.cwd_path.setToolTip(cwd)

        self.files_list.clear()
        try:
            entries = sorted(os.listdir(cwd), key=str.casefold)
        except Exception as e:
            self.files_list.addItem(f"Could not list files: {e}")
            self.files_list.setEnabled(False)
            return

        self.files_list.setEnabled(True)
        file_names = [
            name for name in entries if os.path.isfile(os.path.join(cwd, name))
        ]
        if not file_names:
            self.files_list.addItem("(No files in current directory)")
            self.files_list.setEnabled(False)
            return

        self.files_list.addItems(file_names)

    def _choose_working_directory(self):
        start_dir = os.getcwd()
        selected = QFileDialog.getExistingDirectory(
            self,
            "Select Working Directory",
            start_dir,
        )
        if not selected:
            return

        try:
            os.chdir(selected)
        except Exception as e:
            QMessageBox.critical(self, "Could not change directory", str(e))
            return

        self.refresh_working_directory()
        self.working_directory_changed.emit(os.getcwd())

    def refresh(self, db):
        self.tree.clear()
        tables = db.get_tables()

        if not tables:
            self._show_empty(True)
            return

        self._show_empty(False)
        bold = QFont()
        bold.setBold(True)
        grey = QColor("#888888")

        for table_name in tables:
            table_item = QTreeWidgetItem([table_name, ""])
            table_item.setFont(0, bold)
            table_item.setData(0, Qt.ItemDataRole.UserRole, "table")
            table_item.setToolTip(0, f"Double-click to insert '{table_name}' into editor")

            for col_name, col_type in db.get_columns(table_name):
                col_item = QTreeWidgetItem([col_name, col_type])
                col_item.setForeground(1, grey)
                col_item.setData(0, Qt.ItemDataRole.UserRole, "column")
                table_item.addChild(col_item)

            self.tree.addTopLevelItem(table_item)
            table_item.setExpanded(True)

        self.tree.resizeColumnToContents(0)

    def clear(self):
        self.tree.clear()
        self._show_empty(True)

    def _show_empty(self, show: bool):
        self.tree.setVisible(not show)
        self._empty_label.setVisible(show)

    def _on_double_click(self, item: QTreeWidgetItem, column: int):
        if item.data(0, Qt.ItemDataRole.UserRole) == "table":
            self.table_double_clicked.emit(item.text(0))
