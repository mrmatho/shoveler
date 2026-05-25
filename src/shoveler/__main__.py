import sys
from PySide6.QtWidgets import QApplication

try:
    from .main_window import MainWindow
except ImportError:
    # PyInstaller may execute this file as a top-level script during startup.
    from shoveler.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
