import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

try:
    from .main_window import MainWindow
except ImportError:
    # PyInstaller may execute this file as a top-level script during startup.
    from shoveler.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    icon_path = Path(__file__).resolve().parent / "assets" / "shoveler.ico"
    app_icon = QIcon(str(icon_path))
    app.setWindowIcon(app_icon)
    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
