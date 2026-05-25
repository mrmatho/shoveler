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
        self.open_btn = QPushButton("Open DB File…")
        self.open_btn.setFixedWidth(110)
        self.open_btn.clicked.connect(self._on_open_file)
        layout.addWidget(self.open_btn)

        self.memory_btn = QPushButton("New Blank DB")
        self.memory_btn.setFixedWidth(105)
        self.memory_btn.clicked.connect(self.memory_requested.emit)
        layout.addWidget(self.memory_btn)

        self.checkpoint_btn = QPushButton("Checkpoint")
        self.checkpoint_btn.setFixedWidth(95)
        self.checkpoint_btn.setToolTip(
            "Flush the write-ahead log to disk (file databases only)"
        )
        self.checkpoint_btn.clicked.connect(self.checkpoint_requested.emit)
        layout.addWidget(self.checkpoint_btn)

        self._set_state_disconnected()

    # ── Public state setters ────────────────────────────────────────────────

    def set_file_mode(self, path: str):
        filename = os.path.basename(path)
        self._apply(
            colour=COLOUR_FILE,
            text=f"<b>{filename}</b>  <span style='color:#888'>({path})</span>",
            checkpoint_enabled=True,
            show_save_inline=False,
        )

    def set_memory_mode(self):
        self._apply(
            colour=COLOUR_MEMORY,
            text="<b>In-memory</b>  <span style='color:#888'>(unsaved — data is lost when closed)</span>",
            checkpoint_enabled=False,
            show_save_inline=True,
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
        )

    def _apply(
        self,
        colour: str,
        text: str,
        checkpoint_enabled: bool,
        show_save_inline: bool,
    ):
        self.dot.setStyleSheet(f"font-size: 18px; color: {colour};")
        self.db_label.setText(text)
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
