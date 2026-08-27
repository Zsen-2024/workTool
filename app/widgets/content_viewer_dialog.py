"""通用内容放大查看对话框。"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from app.widgets.markdown_styles import configure_markdown_view, set_markdown_content


class ContentViewerDialog(QDialog):
    """在大窗口中查看 Markdown 或纯文本内容。"""

    def __init__(
        self,
        title: str,
        content: str,
        content_type: str = "markdown",
        parent=None,
    ):
        super().__init__(parent)
        self._content = content
        self._content_type = content_type
        self.setWindowTitle(title)
        self.setMinimumSize(720, 520)
        self.resize(980, 760)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowMinimizeButtonHint
        )
        self._build_ui(content)

    def _build_ui(self, content: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(self.windowTitle())
        title.setObjectName("toolTitle")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        if self._content_type == "markdown":
            viewer = QTextBrowser()
            viewer.setObjectName("markdownView")
            viewer.setOpenExternalLinks(True)
            configure_markdown_view(viewer)
            set_markdown_content(viewer, content)
        else:
            viewer = QPlainTextEdit()
            viewer.setObjectName("httpEditor")
            font = QFont("Consolas")
            font.setStyleHint(QFont.Monospace)
            font.setPointSize(11)
            viewer.setFont(font)
            viewer.setPlainText(content)
            viewer.setReadOnly(True)

        layout.addWidget(viewer, stretch=1)

        actions = QHBoxLayout()
        actions.addStretch()

        copy_btn = QPushButton("复制")
        copy_btn.clicked.connect(self._copy_content)
        actions.addWidget(copy_btn)

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        actions.addWidget(close_btn)

        layout.addLayout(actions)

    def _copy_content(self) -> None:
        QApplication.clipboard().setText(self._content)
