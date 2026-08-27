from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QLabel, QListWidget, QListWidgetItem, QVBoxLayout


class Sidebar(QFrame):
    """左侧工具列表。"""

    tool_selected = pyqtSignal(int)

    def __init__(self, tool_names: list[str], parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("WorkTool")
        title.setObjectName("appTitle")
        layout.addWidget(title)

        section = QLabel("工具箱")
        section.setObjectName("sidebarSection")
        layout.addWidget(section)

        self._list = QListWidget()
        self._list.setFocusPolicy(Qt.NoFocus)
        for name in tool_names:
            self._list.addItem(QListWidgetItem(name))
        self._list.setCurrentRow(0)
        self._list.currentRowChanged.connect(self.tool_selected.emit)
        layout.addWidget(self._list, stretch=1)

    def select_tool(self, index: int) -> None:
        if 0 <= index < self._list.count():
            self._list.setCurrentRow(index)
