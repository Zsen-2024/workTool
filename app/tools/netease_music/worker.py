"""网易云请求后台线程。"""

from __future__ import annotations

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from app.tools.netease_music import client


class NeteaseWorker(QThread):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, kind: str, timeout: int = 30, parent=None, **kwargs):
        super().__init__(parent)
        self._kind = kind
        self._timeout = timeout
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            if self._kind == "playlist":
                result = client.fetch_playlist_songs(
                    int(self._kwargs["playlist_id"]),
                    page=int(self._kwargs.get("page", 1)),
                    timeout=self._timeout,
                )
            elif self._kind == "search":
                result = client.search_songs(
                    str(self._kwargs.get("keyword", "")),
                    page=int(self._kwargs.get("page", 1)),
                    timeout=self._timeout,
                )
            elif self._kind == "url":
                result = client.fetch_song_url(
                    int(self._kwargs["song_id"]),
                    timeout=self._timeout,
                )
            else:
                raise ValueError(f"未知请求类型：{self._kind}")
            self.finished.emit(result)
        except ValueError as exc:
            self.failed.emit(str(exc))
        except LookupError as exc:
            self.failed.emit(str(exc))
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            self.failed.emit(f"HTTP {status}：{exc}")
        except requests.RequestException as exc:
            self.failed.emit(f"网络请求失败：{exc}")
        except Exception as exc:
            self.failed.emit(f"未知错误：{exc}")
