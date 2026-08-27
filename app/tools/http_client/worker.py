"""HTTP 请求后台线程。"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

import requests
from PyQt5.QtCore import QThread, pyqtSignal


@dataclass
class HttpResult:
    status_code: int
    reason: str
    elapsed_ms: float
    response_headers: Dict[str, str]
    body: str
    body_bytes: int
    url: str


class HttpWorker(QThread):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[str],
        timeout: int = 30,
        verify_ssl: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._method = method.upper()
        self._url = url
        self._headers = headers
        self._body = body
        self._timeout = timeout
        self._verify_ssl = verify_ssl

    def run(self) -> None:
        try:
            kwargs = {
                "method": self._method,
                "url": self._url,
                "headers": self._headers,
                "timeout": self._timeout,
                "verify": self._verify_ssl,
                "allow_redirects": True,
            }
            if self._body is not None and self._method not in {"GET", "HEAD"}:
                kwargs["data"] = self._body.encode("utf-8")

            start = time.perf_counter()
            response = requests.request(**kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000

            content = response.content
            body_bytes = len(content)
            try:
                body_text = content.decode(response.encoding or "utf-8", errors="replace")
            except LookupError:
                body_text = content.decode("utf-8", errors="replace")

            result = HttpResult(
                status_code=response.status_code,
                reason=response.reason,
                elapsed_ms=elapsed_ms,
                response_headers=dict(response.headers),
                body=body_text,
                body_bytes=body_bytes,
                url=str(response.url),
            )
            self.finished.emit(result)
        except requests.exceptions.SSLError as exc:
            self.failed.emit(f"SSL 证书验证失败：{exc}")
        except requests.exceptions.ConnectionError as exc:
            self.failed.emit(f"连接失败：{exc}")
        except requests.exceptions.Timeout:
            self.failed.emit(f"请求超时（>{self._timeout}s）")
        except requests.exceptions.RequestException as exc:
            self.failed.emit(f"请求失败：{exc}")
        except Exception as exc:
            self.failed.emit(f"未知错误：{exc}")
