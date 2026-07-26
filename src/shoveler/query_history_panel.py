from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

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
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.setSpacing(6)
        self.list_widget.setUniformItemSizes(False)
        self.list_widget.setStyleSheet("font-size: 12px;")
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)

        self._empty_label = QLabel(QUERY_HISTORY_EMPTY)
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._empty_label.setStyleSheet("font-size: 11px; padding: 8px;")
        layout.addWidget(self._empty_label)

        self._apply_list_styles()
        self.set_queries([])

    def set_theme(self, theme: str):
        self._theme = (theme or "").strip().lower()
        self._apply_list_styles()

    def set_queries(self, queries: list[str]):
        self.list_widget.clear()
        for query in queries:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, query)
            item.setToolTip(query)
            card = self._build_query_card(query)
            item.setSizeHint(card.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, card)

        has_items = self.list_widget.count() > 0
        self.list_widget.setVisible(has_items)
        self._empty_label.setVisible(not has_items)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        query = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(query, str) and query.strip():
            self.query_double_clicked.emit(query)

    def _build_query_card(self, query: str) -> QFrame:
        card = QFrame()
        card.setObjectName("queryHistoryCard")
        card.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(0)

        text = QLabel(query)
        text.setObjectName("queryHistoryText")
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(text)

        return card

    def _apply_list_styles(self):
        palette = {
            "light": {
                "border": "#d7deea",
                "background": "#f8fbff",
                "hover": "#eef4fc",
            },
            "dark": {
                "border": "#3b4659",
                "background": "#232c3b",
                "hover": "#2b3647",
            },
            "vivid": {
                "border": "#5f70a8",
                "background": "#2a3158",
                "hover": "#364074",
            },
        }.get(self._theme, {
            "border": "#d7deea",
            "background": "#f8fbff",
            "hover": "#eef4fc",
        })

        self.list_widget.setStyleSheet(
            "\n".join(
                [
                    "QListWidget { font-size: 12px; border: 1px solid %s; border-radius: 4px; }" % palette["border"],
                    "QListWidget::item { border: none; padding: 0px; margin: 0px; }",
                    "QListWidget::item:selected { background: transparent; }",
                    "QFrame#queryHistoryCard { border: 1px solid %s; border-radius: 6px; background: %s; }" % (palette["border"], palette["background"]),
                    "QFrame#queryHistoryCard:hover { background: %s; }" % palette["hover"],
                    "QLabel#queryHistoryText { font-size: 12px; }",
                ]
            )
        )
