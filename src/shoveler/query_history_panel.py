from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from .config.text import QUERY_HISTORY_EMPTY, QUERY_HISTORY_HEADING


class QueryHistoryPanel(QWidget):
    query_double_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "light"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(4)

        heading = QLabel(QUERY_HISTORY_HEADING)
        heading.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(heading)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet("font-size: 12px;")
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)

        self._empty_label = QLabel(QUERY_HISTORY_EMPTY)
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._empty_label.setStyleSheet("font-size: 11px; padding: 8px;")
        layout.addWidget(self._empty_label)

        self.set_queries([])

    def set_theme(self, theme: str):
        self._theme = (theme or "").strip().lower()

    def set_queries(self, queries: list[str]):
        self.list_widget.clear()
        for query in queries:
            item = QListWidgetItem(self._item_label(query))
            item.setData(Qt.ItemDataRole.UserRole, query)
            item.setToolTip(query)
            self.list_widget.addItem(item)

        has_items = self.list_widget.count() > 0
        self.list_widget.setVisible(has_items)
        self._empty_label.setVisible(not has_items)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        query = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(query, str) and query.strip():
            self.query_double_clicked.emit(query)

    @staticmethod
    def _item_label(query: str) -> str:
        compact = " ".join(query.split())
        if len(compact) <= 90:
            return compact
        return compact[:87] + "..."
