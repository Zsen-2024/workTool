from PyQt5.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from app.sidebar import Sidebar
from app.tools.registry import get_tools


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WorkTool")
        self.setMinimumSize(960, 640)
        self.resize(1100, 720)

        tool_classes = get_tools()
        tool_names = [cls.tool_name for cls in tool_classes]

        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._sidebar = Sidebar(tool_names)
        root_layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        for tool_cls in tool_classes:
            self._stack.addWidget(tool_cls())
        root_layout.addWidget(self._stack, stretch=1)

        self._sidebar.tool_selected.connect(self._stack.setCurrentIndex)

        status = self.statusBar()
        status.showMessage("WorkTool 工具箱")
