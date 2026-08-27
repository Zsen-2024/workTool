import json
from pathlib import Path

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from app.tools.base import BaseToolWidget
from app.widgets.content_viewer_dialog import ContentViewerDialog
from app.widgets.double_click_expand import install_double_click_expand

MAX_TEXT_BYTES = 5 * 1024 * 1024
INDENT = 2


class JsonFormatterWidget(BaseToolWidget):
    tool_id = "json_formatter"
    tool_name = "JSON 格式化"

    def get_title(self) -> str:
        return self.tool_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel(self.get_title())
        title.setObjectName("toolTitle")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        btn_format = QPushButton("格式化")
        btn_format.setObjectName("primaryButton")
        btn_format.clicked.connect(self._format_json)
        toolbar.addWidget(btn_format)

        btn_minify = QPushButton("压缩")
        btn_minify.clicked.connect(self._minify_json)
        toolbar.addWidget(btn_minify)

        btn_validate = QPushButton("校验")
        btn_validate.clicked.connect(self._validate_json)
        toolbar.addWidget(btn_validate)

        btn_paste = QPushButton("粘贴")
        btn_paste.clicked.connect(self._paste_clipboard)
        toolbar.addWidget(btn_paste)

        btn_open = QPushButton("打开文件")
        btn_open.clicked.connect(self._open_file)
        toolbar.addWidget(btn_open)

        btn_copy = QPushButton("复制")
        btn_copy.clicked.connect(self._copy_result)
        toolbar.addWidget(btn_copy)

        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self._clear)
        toolbar.addWidget(btn_clear)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        self._editor = QPlainTextEdit()
        self._editor.setObjectName("jsonEditor")
        self._editor.setPlaceholderText("在此粘贴或输入 JSON，或点击「打开文件」导入…")
        font = QFont("Consolas")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(11)
        self._editor.setFont(font)
        install_double_click_expand(self._editor, self._expand_editor)
        layout.addWidget(self._editor, stretch=1)

        self._status = QLabel("就绪")
        self._status.setObjectName("statusInfo")
        layout.addWidget(self._status)

        self._editor.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self) -> None:
        text = self._editor.toPlainText()
        if not text.strip():
            self._set_status("就绪", "info")
            return
        char_count = len(text)
        self._set_status(f"字符数：{char_count:,}", "info")

    def _get_text(self) -> str:
        return self._editor.toPlainText()

    def _set_text(self, text: str) -> None:
        self._editor.setPlainText(text)

    def _check_size(self, text: str) -> bool:
        if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
            self._set_status("内容过大（超过 5MB），请缩小后再试", "error")
            return False
        return True

    def _parse_json(self, text: str):
        stripped = text.strip()
        if not stripped:
            raise ValueError("请输入 JSON")
        return json.loads(stripped)

    def _set_status(self, message: str, level: str = "info") -> None:
        object_names = {"info": "statusInfo", "ok": "statusOk", "error": "statusError"}
        self._status.setObjectName(object_names.get(level, "statusInfo"))
        self._status.setText(message)
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

    def _format_json(self) -> None:
        text = self._get_text()
        if not self._check_size(text):
            return
        try:
            data = self._parse_json(text)
            formatted = json.dumps(data, ensure_ascii=False, indent=INDENT)
            self._set_text(formatted)
            self._set_status("格式化成功", "ok")
        except json.JSONDecodeError as exc:
            self._set_status(self._format_json_error(exc), "error")
        except ValueError as exc:
            self._set_status(str(exc), "error")

    def _minify_json(self) -> None:
        text = self._get_text()
        if not self._check_size(text):
            return
        try:
            data = self._parse_json(text)
            minified = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            self._set_text(minified)
            self._set_status("压缩成功", "ok")
        except json.JSONDecodeError as exc:
            self._set_status(self._format_json_error(exc), "error")
        except ValueError as exc:
            self._set_status(str(exc), "error")

    def _validate_json(self) -> None:
        text = self._get_text()
        if not self._check_size(text):
            return
        try:
            self._parse_json(text)
            self._set_status("JSON 语法正确", "ok")
        except json.JSONDecodeError as exc:
            self._set_status(self._format_json_error(exc), "error")
        except ValueError as exc:
            self._set_status(str(exc), "error")

    def _paste_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            self._set_status("剪贴板为空", "error")
            return
        if not self._check_size(text):
            return
        self._set_text(text)
        self._set_status("已从剪贴板粘贴", "ok")

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "打开 JSON 文件",
            "",
            "JSON 文件 (*.json);;文本文件 (*.txt);;所有文件 (*.*)",
        )
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            self._set_status("文件编码不是 UTF-8，请转换后重试", "error")
            return
        except OSError as exc:
            self._set_status(f"读取文件失败：{exc}", "error")
            return

        if not self._check_size(content):
            return
        self._set_text(content)
        self._set_status(f"已加载：{Path(path).name}", "ok")

    def _copy_result(self) -> None:
        text = self._get_text()
        if not text.strip():
            self._set_status("没有可复制的内容", "error")
            return
        QApplication.clipboard().setText(text)
        self._set_status("已复制到剪贴板", "ok")

    def _expand_editor(self) -> None:
        text = self._get_text()
        if not text.strip():
            self._set_status("没有可放大的内容", "error")
            return
        ContentViewerDialog(
            "JSON 内容",
            text,
            content_type="text",
            parent=self.window(),
        ).exec_()

    def _clear(self) -> None:
        self._editor.clear()
        self._set_status("已清空", "info")

    @staticmethod
    def _format_json_error(exc: json.JSONDecodeError) -> str:
        return f"JSON 语法错误（第 {exc.lineno} 行，第 {exc.colno} 列）：{exc.msg}"
