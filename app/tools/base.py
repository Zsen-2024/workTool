from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget


class _QtABCMeta(type(QObject), ABCMeta):
    pass


class BaseToolWidget(QWidget, metaclass=_QtABCMeta):
    """所有工具的基类，提供统一标识与标题。"""

    tool_id: str = ""
    tool_name: str = ""

    @abstractmethod
    def get_title(self) -> str:
        """返回工具在侧栏与标题栏显示的名称。"""
