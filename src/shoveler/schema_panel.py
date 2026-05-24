from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor


class SchemaPanel(QWidget):
    table_double_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(4)

        heading = QLabel("Schema")
        heading.setStyleSheet("font-weight: bold; font-size: 12px; color: #555;")
        layout.addWidget(heading)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Name", "Type"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setStyleSheet("font-size: 12px;")
        self.tree.header().setDefaultSectionSize(100)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree)

        self._empty_label = QLabel("Open a database\nto see its tables.")
        self._empty_label.setStyleSheet("color: #aaa; font-size: 11px; padding: 8px;")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._empty_label)

        self._show_empty(True)

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
