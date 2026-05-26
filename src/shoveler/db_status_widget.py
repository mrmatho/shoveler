import os

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QFrame,
)
from PySide6.QtCore import Signal, Qt


# Colour constants — change here to restyle the indicator globally
COLOUR_FILE   = "#2a9d2a"   # green   → file-backed database
COLOUR_MEMORY = "#e6a817"   # amber   → in-memory (unsaved)
COLOUR_NONE   = "#999999"   # grey    → nothing connected
MAX_STATUS_PATH_LENGTH = 60


class DatabaseStatusWidget(QFrame):
    """
    Toolbar-level widget showing connection state with a colour-coded dot.

    Signals:
        file_opened(path)      — user selected a .duckdb file
        memory_requested()     — user clicked New In-Memory
        checkpoint_requested() — user clicked Checkpoint
    """

    file_opened = Signal(str)
    memory_requested = Signal()
    checkpoint_requested = Signal()
    save_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "light"
        self._secondary_text_colour = "#6b7280"
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(38)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)

        # Colour dot
        self.dot = QLabel("●")
        self.dot.setFixedWidth(16)
        self.dot.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.dot)

        # Status text
        self.db_label = QLabel()
        self.db_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.db_label)

        self.save_inline_btn = QPushButton("Save Database As...")
        self.save_inline_btn.setFixedHeight(24)
        self.save_inline_btn.setVisible(False)
        self.save_inline_btn.clicked.connect(self.save_requested.emit)
        layout.addWidget(self.save_inline_btn)

        layout.addStretch()

        # Buttons
        self.open_btn = QPushButton("Open DB File")
        self.open_btn.setFixedWidth(110)
        self.open_btn.clicked.connect(self._on_open_file)
        layout.addWidget(self.open_btn)

        self.memory_btn = QPushButton("New Blank DB")
        self.memory_btn.setFixedWidth(105)
        self.memory_btn.clicked.connect(self.memory_requested.emit)
        layout.addWidget(self.memory_btn)

        self.checkpoint_btn = QPushButton("Checkpoint")
        self.checkpoint_btn.setFixedWidth(95)
        self.checkpoint_btn.setToolTip("Save pending (WAL) changes to the DB file.")
        self.checkpoint_btn.clicked.connect(self.checkpoint_requested.emit)
        layout.addWidget(self.checkpoint_btn)

        self._set_state_disconnected()

    def set_theme(self, theme: str):
        self._theme = (theme or "").strip().lower()
        if self._theme == "dark":
            self._secondary_text_colour = "#a8b5c8"
        elif self._theme == "vivid":
            self._secondary_text_colour = "#b8c6ff"
        else:
            self._secondary_text_colour = "#6b7280"

    # ── Public state setters ────────────────────────────────────────────────

    def set_file_mode(self, path: str):
        filename = os.path.basename(path)
        if len(path) > MAX_STATUS_PATH_LENGTH:
            text = f"<b>{filename}</b>"
        else:
            text = (
                f"<b>{filename}</b>  "
                f"<span style='color:{self._secondary_text_colour}'>({path})</span>"
            )
        self._apply(
            colour=COLOUR_FILE,
            text=text,
            checkpoint_enabled=True,
            show_save_inline=False,
            label_tooltip=path,
        )

    def set_memory_mode(self):
        self._apply(
            colour=COLOUR_MEMORY,
            text=(
                "<b>In-memory</b>  "
                f"<span style='color:{self._secondary_text_colour}'>"
                "(unsaved — data is lost when closed)</span>"
            ),
            checkpoint_enabled=False,
            show_save_inline=True,
            label_tooltip="",
        )

    def notify_checkpoint_ok(self):
        """Brief visual confirmation after a successful checkpoint."""
        current = self.db_label.text()
        # Append a transient tick — main window resets this on next open
        if "✓" not in current:
            self.db_label.setText(current + "  ✓")

    # ── Internals ───────────────────────────────────────────────────────────

    def _set_state_disconnected(self):
        self._apply(
            colour=COLOUR_NONE,
            text="No database connected",
            checkpoint_enabled=False,
            show_save_inline=False,
            label_tooltip="",
        )

    def _apply(
        self,
        colour: str,
        text: str,
        checkpoint_enabled: bool,
        show_save_inline: bool,
        label_tooltip: str,
    ):
        self.dot.setStyleSheet(f"font-size: 18px; color: {colour};")
        self.db_label.setText(text)
        self.db_label.setToolTip(label_tooltip)
        self.checkpoint_btn.setVisible(checkpoint_enabled)
        self.checkpoint_btn.setEnabled(checkpoint_enabled)
        self.save_inline_btn.setVisible(show_save_inline)

    def _on_open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open DuckDB Database",
            "",
            "DuckDB Files (*.duckdb *.db);;All Files (*)",
        )
        if path:
            self.file_opened.emit(path)
