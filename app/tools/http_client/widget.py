"""HTTP / HTTPS 接口调试工具。"""

from __future__ import annotations

import json
from typing import Dict, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.tools.base import BaseToolWidget
from app.tools.http_client.worker import HttpResult, HttpWorker
from app.widgets.content_viewer_dialog import ContentViewerDialog
from app.widgets.double_click_expand import install_double_click_expand

MAX_BODY_DISPLAY = 5 * 1024 * 1024
METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
BODY_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def parse_headers(text: str) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if key:
            headers[key] = value
    return headers


def format_headers(headers: Dict[str, str]) -> str:
    return "\n".join(f"{k}: {v}" for k, v in headers.items())


def try_format_json(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return text
    try:
        return json.dumps(json.loads(stripped), ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        return text


def format_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.2f} MB"


class HttpClientWidget(BaseToolWidget):
    tool_id = "http_client"
    tool_name = "接口调试"

    def get_title(self) -> str:
        return self.tool_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: Optional[HttpWorker] = None
        self._build_ui()
        self._method.currentTextChanged.connect(self._on_method_changed)
        self._on_method_changed(self._method.currentText())

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

        # 请求行：方法 + URL + 发送
        request_bar = QHBoxLayout()
        request_bar.setSpacing(8)

        self._method = QComboBox()
        self._method.setObjectName("methodCombo")
        self._method.addItems(METHODS)
        self._method.setCurrentText("GET")
        self._method.setFixedWidth(110)
        request_bar.addWidget(self._method)

        self._url = QLineEdit()
        self._url.setObjectName("urlInput")
        self._url.setPlaceholderText("https://api.example.com/users")
        request_bar.addWidget(self._url, stretch=1)

        self._send_btn = QPushButton("发送")
        self._send_btn.setObjectName("primaryButton")
        self._send_btn.setFixedWidth(88)
        self._send_btn.clicked.connect(self._send_request)
        request_bar.addWidget(self._send_btn)

        layout.addLayout(request_bar)

        # 选项行
        options = QHBoxLayout()
        options.setSpacing(16)

        timeout_label = QLabel("超时 (秒)")
        options.addWidget(timeout_label)

        timeout_box = QHBoxLayout()
        timeout_box.setSpacing(4)

        btn_timeout_down = QPushButton("−")
        btn_timeout_down.setObjectName("stepButton")
        btn_timeout_down.setFixedSize(28, 28)
        btn_timeout_down.setToolTip("减少 1 秒")
        timeout_box.addWidget(btn_timeout_down)

        self._timeout = QSpinBox()
        self._timeout.setObjectName("timeoutSpin")
        self._timeout.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._timeout.setRange(1, 300)
        self._timeout.setValue(30)
        self._timeout.setFixedWidth(52)
        self._timeout.setAlignment(Qt.AlignCenter)
        self._timeout.setToolTip("请求最长等待时间（秒）")
        timeout_box.addWidget(self._timeout)

        btn_timeout_up = QPushButton("+")
        btn_timeout_up.setObjectName("stepButton")
        btn_timeout_up.setFixedSize(28, 28)
        btn_timeout_up.setToolTip("增加 1 秒")
        timeout_box.addWidget(btn_timeout_up)

        btn_timeout_down.clicked.connect(lambda: self._timeout.setValue(max(1, self._timeout.value() - 1)))
        btn_timeout_up.clicked.connect(lambda: self._timeout.setValue(min(300, self._timeout.value() + 1)))

        options.addLayout(timeout_box)

        self._verify_ssl = QCheckBox("验证 SSL 证书")
        self._verify_ssl.setChecked(True)
        self._verify_ssl.setToolTip(
            "勾选：校验 HTTPS 服务器证书是否合法（生产环境推荐）\n"
            "不勾选：跳过证书校验（仅用于内网自签证书、测试环境）"
        )

        options.addStretch()
        layout.addLayout(options)

        splitter = QSplitter(Qt.Vertical)
        splitter.setObjectName("httpSplitter")

        # 请求区
        request_panel = QWidget()
        request_layout = QVBoxLayout(request_panel)
        request_layout.setContentsMargins(0, 0, 0, 0)
        request_layout.setSpacing(8)

        req_label = QLabel("请求")
        req_label.setObjectName("sectionLabel")
        request_layout.addWidget(req_label)

        self._req_tabs = QTabWidget()
        self._req_tabs.setObjectName("httpTabs")
        self._req_tabs.setDocumentMode(True)

        self._headers_edit = QPlainTextEdit()
        self._headers_edit.setObjectName("httpEditor")
        self._headers_edit.setFont(self._mono_font())
        self._headers_edit.setPlaceholderText(
            "每行一个 Header，格式：Key: Value\n"
            "示例：\n"
            "Content-Type: application/json\n"
            "Authorization: Bearer your-token"
        )
        self._headers_edit.setPlainText("Content-Type: application/json")
        install_double_click_expand(
            self._headers_edit,
            lambda: self._expand_content("请求 Headers", self._headers_edit.toPlainText()),
        )
        self._req_tabs.addTab(self._headers_edit, "Headers")

        self._body_edit = QPlainTextEdit()
        self._body_edit.setObjectName("httpEditor")
        self._body_edit.setFont(self._mono_font())
        self._body_edit.setPlaceholderText('{"name": "test"}')
        install_double_click_expand(
            self._body_edit,
            lambda: self._expand_content("请求 Body", self._body_edit.toPlainText()),
        )
        self._req_tabs.addTab(self._body_edit, "Body")

        request_layout.addWidget(self._req_tabs)
        splitter.addWidget(request_panel)

        # 响应区
        response_panel = QWidget()
        response_layout = QVBoxLayout(response_panel)
        response_layout.setContentsMargins(0, 0, 0, 0)
        response_layout.setSpacing(8)

        resp_header = QHBoxLayout()
        resp_label = QLabel("响应")
        resp_label.setObjectName("sectionLabel")
        resp_header.addWidget(resp_label)
        resp_header.addStretch()

        self._format_resp_btn = QPushButton("格式化 JSON")
        self._format_resp_btn.clicked.connect(self._format_response_json)
        resp_header.addWidget(self._format_resp_btn)

        self._copy_resp_btn = QPushButton("复制 Body")
        self._copy_resp_btn.clicked.connect(self._copy_response)
        resp_header.addWidget(self._copy_resp_btn)

        response_layout.addLayout(resp_header)

        self._meta = QLabel("等待发送请求…")
        self._meta.setObjectName("statusInfo")
        response_layout.addWidget(self._meta)

        self._resp_tabs = QTabWidget()
        self._resp_tabs.setObjectName("httpTabs")
        self._resp_tabs.setDocumentMode(True)

        self._resp_body = QPlainTextEdit()
        self._resp_body.setObjectName("httpEditor")
        self._resp_body.setFont(self._mono_font())
        self._resp_body.setReadOnly(True)
        self._resp_body.setPlaceholderText("响应 Body 将显示在这里")
        install_double_click_expand(
            self._resp_body,
            lambda: self._expand_content("响应 Body", self._resp_body.toPlainText()),
        )
        self._resp_tabs.addTab(self._resp_body, "Body")

        self._resp_headers = QPlainTextEdit()
        self._resp_headers.setObjectName("httpEditor")
        self._resp_headers.setFont(self._mono_font())
        self._resp_headers.setReadOnly(True)
        install_double_click_expand(
            self._resp_headers,
            lambda: self._expand_content("响应 Headers", self._resp_headers.toPlainText()),
        )
        self._resp_tabs.addTab(self._resp_headers, "Headers")

        response_layout.addWidget(self._resp_tabs)
        splitter.addWidget(response_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([280, 360])

        layout.addWidget(splitter, stretch=1)

        self._status = QLabel("就绪")
        self._status.setObjectName("statusInfo")
        layout.addWidget(self._status)

    def _on_method_changed(self, method: str) -> None:
        has_body = method in BODY_METHODS
        self._body_edit.setEnabled(has_body)
        if has_body:
            self._body_edit.setPlaceholderText('{"name": "test"}')
        else:
            self._body_edit.setPlaceholderText(f"{method} 请求不会发送 Body，可切换为 POST 等方法")

    def _set_status(self, message: str, level: str = "info") -> None:
        names = {"info": "statusInfo", "ok": "statusOk", "error": "statusError"}
        self._status.setObjectName(names.get(level, "statusInfo"))
        self._status.setText(message)
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

    def _set_loading(self, loading: bool) -> None:
        self._send_btn.setEnabled(not loading)
        self._send_btn.setText("发送中…" if loading else "发送")

    def _send_request(self) -> None:
        url = self._url.text().strip()
        if not url:
            self._set_status("请输入请求 URL", "error")
            return
        if not url.startswith(("http://", "https://")):
            self._set_status("URL 需以 http:// 或 https:// 开头", "error")
            return

        if self._worker and self._worker.isRunning():
            self._set_status("请求进行中，请稍候", "error")
            return

        method = self._method.currentText()
        headers = parse_headers(self._headers_edit.toPlainText())
        body: Optional[str] = None
        if method in BODY_METHODS:
            body_text = self._body_edit.toPlainText()
            if body_text.strip():
                body = body_text

        self._set_loading(True)
        self._set_status(f"正在发送 {method} 请求…", "info")
        self._meta.setText("请求发送中…")

        self._worker = HttpWorker(
            method=method,
            url=url,
            headers=headers,
            body=body,
            timeout=self._timeout.value(),
            verify_ssl=self._verify_ssl.isChecked(),
        )
        self._worker.finished.connect(self._on_request_finished)
        self._worker.failed.connect(self._on_request_failed)
        self._worker.start()

    def _on_request_finished(self, result: HttpResult) -> None:
        self._set_loading(False)
        self._worker = None

        status_level = "ok" if 200 <= result.status_code < 400 else "error"
        self._meta.setObjectName("statusOk" if status_level == "ok" else "statusError")
        self._meta.setText(
            f"{result.status_code} {result.reason}  ·  "
            f"{result.elapsed_ms:.0f} ms  ·  "
            f"{format_size(result.body_bytes)}  ·  "
            f"{result.url}"
        )
        self._meta.style().unpolish(self._meta)
        self._meta.style().polish(self._meta)

        body = result.body
        if len(body.encode("utf-8")) > MAX_BODY_DISPLAY:
            body = body[:MAX_BODY_DISPLAY] + "\n\n…（响应过大，已截断显示）"

        self._resp_body.setPlainText(body)
        self._resp_headers.setPlainText(format_headers(result.response_headers))
        self._resp_tabs.setCurrentIndex(0)
        self._set_status("请求完成", "ok")

    def _on_request_failed(self, message: str) -> None:
        self._set_loading(False)
        self._worker = None
        self._meta.setObjectName("statusError")
        self._meta.setText(message)
        self._meta.style().unpolish(self._meta)
        self._meta.style().polish(self._meta)
        self._resp_body.clear()
        self._resp_headers.clear()
        self._set_status(message, "error")

    def _format_response_json(self) -> None:
        text = self._resp_body.toPlainText()
        if not text.strip():
            self._set_status("没有可格式化的响应", "error")
            return
        formatted = try_format_json(text)
        if formatted == text:
            self._set_status("响应不是合法 JSON", "error")
            return
        self._resp_body.setPlainText(formatted)
        self._set_status("响应 JSON 已格式化", "ok")

    def _copy_response(self) -> None:
        text = self._resp_body.toPlainText()
        if not text.strip():
            self._set_status("没有可复制的响应", "error")
            return
        QApplication.clipboard().setText(text)
        self._set_status("响应 Body 已复制", "ok")

    def _expand_content(self, title: str, text: str) -> None:
        if not text.strip():
            self._set_status("没有可放大的内容", "error")
            return
        ContentViewerDialog(
            title,
            text,
            content_type="text",
            parent=self.window(),
        ).exec_()
