import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from app.main_window import MainWindow
from app.resources import asset_path
from app.theme import LIGHT_THEME


def main() -> int:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("WorkTool")
    app.setStyle("Fusion")
    app.setStyleSheet(LIGHT_THEME)

    icon_file = asset_path("icon.ico")
    if icon_file.exists():
        app_icon = QIcon(str(icon_file))
        app.setWindowIcon(app_icon)

    window = MainWindow()
    if icon_file.exists():
        window.setWindowIcon(app_icon)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
