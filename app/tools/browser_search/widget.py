"""浏览器历史与书签检索。"""

from __future__ import annotations

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
)

from app.tools.base import BaseToolWidget
from app.tools.browser_search.browser_data import BrowserEntry, open_url, search_browser_data


class BrowserSearchWidget(BaseToolWidget):
    tool_id = "browser_search"
    tool_name = "网址检索"

    def get_title(self) -> str:
        return self.tool_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[BrowserEntry] = []
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._search)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel(self.get_title())
        title.setObjectName("toolTitle")
        layout.addWidget(title)

        hint = QLabel(
            "检索本机 Chrome / Edge 的浏览历史与书签（只读本地数据）。"
            "输入即搜；留空点击「检索」可浏览全部；单击结果打开链接，右键可复制 URL。"
        )
        hint.setObjectName("statusInfo")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        search_bar = QHBoxLayout()
        search_bar.setSpacing(8)

        self._keyword = QLineEdit()
        self._keyword.setObjectName("urlInput")
        self._keyword.setPlaceholderText("输入关键词，匹配标题或 URL…")
        self._keyword.textChanged.connect(self._schedule_search)
        search_bar.addWidget(self._keyword, stretch=1)

        self._scope = QComboBox()
        self._scope.setObjectName("fieldCombo")
        self._scope.addItem("全部浏览器", "all")
        self._scope.addItem("Chrome", "chrome")
        self._scope.addItem("Edge", "edge")
        self._scope.setMinimumWidth(120)
        self._scope.currentIndexChanged.connect(self._schedule_search)
        search_bar.addWidget(self._scope)

        self._kind = QComboBox()
        self._kind.setObjectName("fieldCombo")
        self._kind.addItem("历史 + 书签", "all")
        self._kind.addItem("仅历史", "history")
        self._kind.addItem("仅书签", "bookmark")
        self._kind.setMinimumWidth(110)
        self._kind.currentIndexChanged.connect(self._schedule_search)
        search_bar.addWidget(self._kind)

        btn_search = QPushButton("检索")
        btn_search.setObjectName("primaryButton")
        btn_search.setFixedWidth(88)
        btn_search.clicked.connect(lambda: self._search(browse_all=True))
        search_bar.addWidget(btn_search)

        layout.addLayout(search_bar)

        self._results = QListWidget()
        self._results.setObjectName("resultList")
        self._results.itemClicked.connect(self._open_item)
        self._results.setContextMenuPolicy(Qt.CustomContextMenu)
        self._results.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self._results, stretch=1)

        self._status = QLabel("就绪 · 输入关键词实时检索，或留空点击「检索」浏览全部")
        self._status.setObjectName("statusInfo")
        layout.addWidget(self._status)

    def _schedule_search(self) -> None:
        self._search_timer.start(300)

    def _set_status(self, message: str, level: str = "info") -> None:
        names = {"info": "statusInfo", "ok": "statusOk", "error": "statusError"}
        self._status.setObjectName(names.get(level, "statusInfo"))
        self._status.setText(message)
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

    def _search(self, browse_all: bool = False) -> None:
        keyword = self._keyword.text().strip()
        self._results.clear()
        self._entries = []

        if not keyword and not browse_all:
            self._set_status("就绪 · 输入关键词实时检索，或留空点击「检索」浏览全部", "info")
            return

        self._entries = search_browser_data(
            keyword=keyword,
            scope=self._scope.currentData(),
            kind=self._kind.currentData(),
            browse_all=browse_all and not keyword,
        )

        if not self._entries:
            if browse_all and not keyword:
                self._set_status("未找到可用的历史或书签数据", "error")
            else:
                self._set_status(f"未找到与「{keyword}」匹配的历史或书签", "error")
            return

        for index, entry in enumerate(self._entries, 1):
            meta = entry.source
            if entry.visited_at:
                meta += f" · {entry.visited_at}"
            text = f"{index}. {entry.title}\n{entry.url}\n{meta}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, entry.url)
            self._results.addItem(item)

        self._set_status(
            f"已列出 {len(self._entries)} 条（最多 200 条）"
            if browse_all and not keyword
            else f"找到 {len(self._entries)} 条结果",
            "ok",
        )

    def _open_item(self, item: QListWidgetItem) -> None:
        url = item.data(Qt.UserRole) or ""
        self._open_url(url)

    def _open_url(self, url: str) -> None:
        if not url:
            self._set_status("请先选择一条结果", "error")
            return
        if not open_url(url):
            self._set_status("URL 无效，无法打开", "error")
            return
        self._set_status(f"已在浏览器打开：{url}", "ok")

    def _copy_url(self, url: str) -> None:
        if not url:
            self._set_status("没有可复制的 URL", "error")
            return
        QApplication.clipboard().setText(url)
        self._set_status("URL 已复制", "ok")

    def _show_context_menu(self, pos) -> None:
        item = self._results.itemAt(pos)
        if not item:
            return

        self._results.setCurrentItem(item)
        url = item.data(Qt.UserRole) or ""

        menu = QMenu(self)
        open_action = menu.addAction("打开链接")
        copy_action = menu.addAction("复制 URL")
        chosen = menu.exec_(self._results.viewport().mapToGlobal(pos))

        if chosen == open_action:
            self._open_url(url)
        elif chosen == copy_action:
            self._copy_url(url)
