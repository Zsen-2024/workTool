"""双击内容区放大查看。"""

from __future__ import annotations

from typing import Callable

from PyQt5.QtCore import QEvent, QObject


class _DoubleClickFilter(QObject):
    def __init__(self, callback: Callable[[], None], parent=None):
        super().__init__(parent)
        self._callback = callback

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonDblClick:
            self._callback()
            return True
        return False


def install_double_click_expand(widget, callback: Callable[[], None]) -> None:
    """为 QPlainTextEdit / QTextBrowser 安装双击放大。"""
    filt = _DoubleClickFilter(callback, widget)
    widget.viewport().installEventFilter(filt)
    widget._double_click_filter = filt  # 保持引用，避免被回收
