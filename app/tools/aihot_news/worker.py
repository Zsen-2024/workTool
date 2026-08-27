"""AIHOT 请求后台线程。"""

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from app.tools.aihot_news.client import AihotRequest, AihotResponse, fetch


class AihotWorker(QThread):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, request: AihotRequest, timeout: int = 30, parent=None):
        super().__init__(parent)
        self._request = request
        self._timeout = timeout

    def run(self) -> None:
        try:
            result = fetch(self._request, timeout=self._timeout)
            self.finished.emit(result)
        except ValueError as exc:
            self.failed.emit(str(exc))
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            self.failed.emit(f"HTTP {status}：{exc}")
        except requests.RequestException as exc:
            self.failed.emit(f"网络请求失败：{exc}")
        except Exception as exc:
            self.failed.emit(f"未知错误：{exc}")
