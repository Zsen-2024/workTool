"""Markdown 预览工具。"""

from __future__ import annotations

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.tools.base import BaseToolWidget
from app.widgets.content_viewer_dialog import ContentViewerDialog
from app.widgets.double_click_expand import install_double_click_expand
from app.widgets.markdown_styles import configure_markdown_view, set_markdown_content


class MarkdownPreviewWidget(BaseToolWidget):
    tool_id = "markdown_preview"
    tool_name = "Markdown 预览"

    def get_title(self) -> str:
        return self.tool_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._render_preview)
        self._build_ui()

    def _mono_font(self) -> QFont:
        font = QFont("Consolas")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(11)
        return font

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel(self.get_title())
        title.setObjectName("toolTitle")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        btn_render = QPushButton("渲染预览")
        btn_render.setObjectName("primaryButton")
        btn_render.clicked.connect(self._render_preview)
        toolbar.addWidget(btn_render)

        btn_paste = QPushButton("粘贴")
        btn_paste.clicked.connect(self._paste)
        toolbar.addWidget(btn_paste)

        btn_copy = QPushButton("复制源码")
        btn_copy.clicked.connect(self._copy_source)
        toolbar.addWidget(btn_copy)

        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self._clear)
        toolbar.addWidget(btn_clear)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("httpSplitter")

        source_container = QWidget()
        source_layout = QVBoxLayout(source_container)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.setSpacing(8)

        source_label = QLabel("Markdown 源码")
        source_label.setObjectName("sectionLabel")
        source_layout.addWidget(source_label)

        self._source = QPlainTextEdit()
        self._source.setObjectName("jsonEditor")
        self._source.setFont(self._mono_font())
        self._source.setPlaceholderText("在此粘贴或输入 Markdown 文本…")
        self._source.textChanged.connect(self._schedule_preview)
        install_double_click_expand(self._source, self._expand_source)
        source_layout.addWidget(self._source)
        splitter.addWidget(source_container)

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(8)

        preview_label = QLabel("渲染预览")
        preview_label.setObjectName("sectionLabel")
        preview_layout.addWidget(preview_label)

        self._preview = QTextBrowser()
        self._preview.setObjectName("markdownView")
        self._preview.setOpenExternalLinks(True)
        configure_markdown_view(self._preview)
        set_markdown_content(self._preview, "*在左侧输入 Markdown，右侧实时预览…*")
        install_double_click_expand(self._preview, self._expand_preview)
        preview_layout.addWidget(self._preview)
        splitter.addWidget(preview_container)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([480, 480])
        layout.addWidget(splitter, stretch=1)

        self._status = QLabel("就绪 · 输入后自动预览")
        self._status.setObjectName("statusInfo")
        layout.addWidget(self._status)

    def _schedule_preview(self) -> None:
        self._preview_timer.start(400)

    def _render_preview(self) -> None:
        text = self._source.toPlainText()
        if not text.strip():
            set_markdown_content(self._preview, "*暂无内容*")
            self._set_status("就绪 · 输入后自动预览", "info")
            return
        set_markdown_content(self._preview, text)
        self._set_status(f"已渲染 · {len(text):,} 字符", "ok")

    def _set_status(self, message: str, level: str = "info") -> None:
        names = {"info": "statusInfo", "ok": "statusOk", "error": "statusError"}
        self._status.setObjectName(names.get(level, "statusInfo"))
        self._status.setText(message)
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

    def _paste(self) -> None:
        text = QApplication.clipboard().text()
        if not text:
            self._set_status("剪贴板为空", "error")
            return
        self._source.setPlainText(text)
        self._set_status("已从剪贴板粘贴", "ok")

    def _copy_source(self) -> None:
        text = self._source.toPlainText()
        if not text.strip():
            self._set_status("没有可复制的内容", "error")
            return
        QApplication.clipboard().setText(text)
        self._set_status("已复制 Markdown 源码", "ok")

    def _clear(self) -> None:
        self._source.clear()
        set_markdown_content(self._preview, "*在左侧输入 Markdown，右侧实时预览…*")
        self._set_status("已清空", "info")

    def _expand_source(self) -> None:
        text = self._source.toPlainText()
        if not text.strip():
            self._set_status("没有可放大的内容", "error")
            return
        ContentViewerDialog("Markdown 源码", text, "text", self.window()).exec_()

    def _expand_preview(self) -> None:
        text = self._source.toPlainText()
        if not text.strip():
            self._set_status("没有可放大的内容", "error")
            return
        ContentViewerDialog("Markdown 预览", text, "markdown", self.window()).exec_()
