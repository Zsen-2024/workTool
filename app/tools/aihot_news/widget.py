"""AIHOT 新闻获取工具界面。"""

from __future__ import annotations

import json
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.tools.aihot_news.client import AihotRequest, ENDPOINTS, CATEGORIES
from app.tools.aihot_news.worker import AihotWorker
from app.tools.base import BaseToolWidget
from app.widgets.content_viewer_dialog import ContentViewerDialog
from app.widgets.double_click_expand import install_double_click_expand
from app.widgets.markdown_styles import configure_markdown_view, set_markdown_content


class AihotNewsWidget(BaseToolWidget):
    tool_id = "aihot_news"
    tool_name = "AIHOT 资讯"

    def get_title(self) -> str:
        return self.tool_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: Optional[AihotWorker] = None
        self._summary_markdown = ""
        self._json_text = ""
        self._build_ui()
        self._endpoint.currentIndexChanged.connect(self._on_endpoint_changed)
        self._on_endpoint_changed()

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

        hint = QLabel("数据来源：AIHOT（https://aihot.virxact.com/）· 匿名只读 API，无需 Key")
        hint.setObjectName("statusInfo")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        top = QHBoxLayout()
        top.setSpacing(8)

        self._endpoint = QComboBox()
        self._endpoint.setObjectName("endpointCombo")
        for key, label in ENDPOINTS.items():
            self._endpoint.addItem(label, key)
        self._endpoint.setMinimumWidth(220)
        self._endpoint.setMinimumHeight(36)
        top.addWidget(self._endpoint)

        self._fetch_btn = QPushButton("获取")
        self._fetch_btn.setObjectName("primaryButton")
        self._fetch_btn.setFixedWidth(88)
        self._fetch_btn.clicked.connect(self._fetch_news)
        top.addWidget(self._fetch_btn)

        self._copy_btn = QPushButton("复制简报")
        self._copy_btn.clicked.connect(self._copy_summary)
        top.addWidget(self._copy_btn)

        top.addStretch()
        layout.addLayout(top)

        self._params_box = QGroupBox("请求参数")
        self._params_box.setObjectName("paramsBox")
        params_layout = QFormLayout(self._params_box)
        params_layout.setLabelAlignment(Qt.AlignRight)
        params_layout.setSpacing(10)

        self._window = QComboBox()
        self._window.setObjectName("fieldCombo")
        self._window.addItem("过去 24 小时", "24h")
        self._window.addItem("过去 7 天", "7d")
        params_layout.addRow("时间范围", self._window)

        self._limit = QSpinBox()
        self._limit.setObjectName("timeoutSpin")
        self._limit.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._limit.setRange(1, 100)
        self._limit.setValue(20)
        self._limit.setFixedWidth(72)
        params_layout.addRow("条数 limit", self._limit)

        self._category = QComboBox()
        self._category.setObjectName("fieldCombo")
        for key, label in CATEGORIES.items():
            self._category.addItem(label, key)
        params_layout.addRow("分类", self._category)

        self._keyword = QLineEdit()
        self._keyword.setObjectName("urlInput")
        self._keyword.setPlaceholderText("可选，如 OpenAI、英伟达")
        params_layout.addRow("关键词 q", self._keyword)

        self._date = QLineEdit()
        self._date.setObjectName("urlInput")
        self._date.setPlaceholderText("YYYY-MM-DD，如 2026-08-27")
        params_layout.addRow("日报日期", self._date)

        self._story_url = QLineEdit()
        self._story_url.setObjectName("urlInput")
        self._story_url.setPlaceholderText("热点事件链接或 publicId")
        params_layout.addRow("事件 ID/链接", self._story_url)

        layout.addWidget(self._params_box)

        self._result_tabs = QTabWidget()
        self._result_tabs.setObjectName("httpTabs")
        self._result_tabs.setDocumentMode(True)

        self._summary_view = QTextBrowser()
        self._summary_view.setObjectName("markdownView")
        self._summary_view.setOpenExternalLinks(True)
        configure_markdown_view(self._summary_view)
        set_markdown_content(self._summary_view, "*点击「获取」加载 AIHOT 资讯简报…*")
        install_double_click_expand(self._summary_view, lambda: self._expand_view("summary"))
        self._result_tabs.addTab(self._summary_view, "简报")

        self._json_view = QPlainTextEdit()
        self._json_view.setObjectName("httpEditor")
        self._json_view.setFont(self._mono_font())
        self._json_view.setReadOnly(True)
        self._json_view.setPlaceholderText("原始 JSON 响应…")
        install_double_click_expand(self._json_view, lambda: self._expand_view("json"))
        self._result_tabs.addTab(self._json_view, "原始 JSON")

        layout.addWidget(self._result_tabs, stretch=1)

        self._status = QLabel("就绪")
        self._status.setObjectName("statusInfo")
        layout.addWidget(self._status)

    def _set_row_visible(self, widget: QWidget, visible: bool) -> None:
        label = self._params_box.layout().labelForField(widget)
        if label:
            label.setVisible(visible)
        widget.setVisible(visible)

    def _on_endpoint_changed(self) -> None:
        endpoint = self._endpoint.currentData()
        is_items = endpoint in {"items_selected", "items_all"}
        is_daily_date = endpoint == "daily_by_date"
        is_daily_index = endpoint == "daily_index"
        is_story = endpoint == "story"

        self._set_row_visible(self._window, is_items)
        self._set_row_visible(self._limit, is_items or is_daily_index)
        self._set_row_visible(self._category, is_items)
        self._set_row_visible(self._keyword, is_items)
        self._set_row_visible(self._date, is_daily_date)
        self._set_row_visible(self._story_url, is_story)

    def _set_status(self, message: str, level: str = "info") -> None:
        names = {"info": "statusInfo", "ok": "statusOk", "error": "statusError"}
        self._status.setObjectName(names.get(level, "statusInfo"))
        self._status.setText(message)
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

    def _set_loading(self, loading: bool) -> None:
        self._fetch_btn.setEnabled(not loading)
        self._fetch_btn.setText("获取中…" if loading else "获取")

    def _build_request(self) -> AihotRequest:
        return AihotRequest(
            endpoint=self._endpoint.currentData(),
            window=self._window.currentData(),
            limit=self._limit.value(),
            category=self._category.currentData() or "",
            keyword=self._keyword.text(),
            date=self._date.text(),
            story_url=self._story_url.text(),
            public_id=self._story_url.text(),
        )

    def _fetch_news(self) -> None:
        if self._worker and self._worker.isRunning():
            self._set_status("请求进行中，请稍候", "error")
            return

        try:
            request = self._build_request()
        except ValueError as exc:
            self._set_status(str(exc), "error")
            return

        self._set_loading(True)
        self._set_status("正在从 AIHOT 获取数据…", "info")

        self._worker = AihotWorker(request)
        self._worker.finished.connect(self._on_fetch_finished)
        self._worker.failed.connect(self._on_fetch_failed)
        self._worker.start()

    def _on_fetch_finished(self, result) -> None:
        self._set_loading(False)
        self._worker = None
        self._summary_markdown = result.formatted
        self._json_text = json.dumps(result.data, ensure_ascii=False, indent=2)
        set_markdown_content(self._summary_view, result.formatted)
        self._json_view.setPlainText(self._json_text)
        self._result_tabs.setCurrentIndex(0)
        self._set_status(f"获取成功 · {result.url}", "ok")

    def _on_fetch_failed(self, message: str) -> None:
        self._set_loading(False)
        self._worker = None
        self._set_status(message, "error")

    def _copy_summary(self) -> None:
        if not self._summary_markdown.strip():
            self._set_status("没有可复制的简报", "error")
            return
        QApplication.clipboard().setText(self._summary_markdown)
        self._set_status("简报已复制到剪贴板", "ok")

    def _expand_view(self, source: str) -> None:
        if source == "summary":
            if not self._summary_markdown.strip():
                self._set_status("没有可放大的简报内容", "error")
                return
            ContentViewerDialog(
                "AIHOT 资讯简报",
                self._summary_markdown,
                content_type="markdown",
                parent=self.window(),
            ).exec_()
            return

        if not self._json_text.strip():
            self._set_status("没有可放大的 JSON 内容", "error")
            return
        ContentViewerDialog(
            "AIHOT 原始 JSON",
            self._json_text,
            content_type="text",
            parent=self.window(),
        ).exec_()
