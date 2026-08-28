# 网易云听歌工具 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 WorkTool 中新增游客模式「网易云听歌」工具：热歌榜 / 新歌榜分页、搜索、应用内播放。

**Architecture:** `app/tools/netease_music/` 插件：`client.py`（weapi 最小客户端）→ `worker.py`（QThread）→ `widget.py`（UI）+ `player.py`（QMediaPlayer）。注册到 `registry.py`。

**Tech Stack:** Python 3.10+、PyQt5（含 QtMultimedia）、requests、标准库 `unittest`（无新增测试框架依赖）

## Global Constraints

- 游客模式，不登录、不持久化 Cookie
- 不自建 / 内嵌 Node API；不引入 pyncm
- 每页固定 30 首；热歌榜 id `3778678`，新歌榜 id `3779629`
- 仅个人学习测试文案；不下载歌曲到本地
- 沿用现有浅色办公风与 `BaseToolWidget` 注册模式
- 提交说明用英文 concise 风格（与仓库近期 commit 一致）

---

## File Structure

| 文件 | 职责 |
|------|------|
| `app/tools/netease_music/__init__.py` | 包标记 |
| `app/tools/netease_music/client.py` | weapi 加密 + 榜单/搜索/播放 URL |
| `app/tools/netease_music/worker.py` | 后台请求线程 |
| `app/tools/netease_music/player.py` | QMediaPlayer 封装 |
| `app/tools/netease_music/widget.py` | 工具页 UI |
| `app/tools/registry.py` | 注册工具 |
| `tests/test_netease_music_client.py` | client 单元测试 |
| `README.md` | 功能概览一行 |

---

### Task 1: client weapi + 数据模型

**Files:**
- Create: `app/tools/netease_music/__init__.py`
- Create: `app/tools/netease_music/client.py`
- Create: `tests/test_netease_music_client.py`

**Interfaces:**
- Produces:
  - `PAGE_SIZE: int = 30`
  - `HOT_PLAYLIST_ID: int = 3778678`
  - `NEW_PLAYLIST_ID: int = 3779629`
  - `@dataclass SongItem(id: int, name: str, artists: str, duration_ms: int)`
  - `@dataclass SongPage(songs: list[SongItem], total: int, page: int, page_size: int)`
  - `fetch_playlist_songs(playlist_id: int, page: int = 1, timeout: int = 30) -> SongPage`
  - `search_songs(keyword: str, page: int = 1, timeout: int = 30) -> SongPage`
  - `fetch_song_url(song_id: int, timeout: int = 30) -> str`（无 URL 时 `raise LookupError("暂无法播放")`）

- [ ] **Step 1: 写失败单测（加密与分页切片可离线测；网络测可 skip）**

```python
# tests/test_netease_music_client.py
import unittest
from unittest.mock import patch, MagicMock

from app.tools.netease_music import client


class TestWeapiEncrypt(unittest.TestCase):
    def test_weapi_payload_has_params_and_encSecKey(self):
        payload = client._weapi_encrypt({"foo": "bar"})
        self.assertIn("params", payload)
        self.assertIn("encSecKey", payload)
        self.assertTrue(payload["params"])
        self.assertTrue(payload["encSecKey"])


class TestPlaylistPaging(unittest.TestCase):
    def test_slice_page(self):
        items = [client.SongItem(i, f"n{i}", "a", 1000) for i in range(1, 71)]
        page2 = client._slice_page(items, page=2, page_size=30, total=70)
        self.assertEqual(len(page2.songs), 30)
        self.assertEqual(page2.songs[0].id, 31)
        self.assertEqual(page2.total, 70)
        self.assertEqual(page2.page, 2)


class TestFetchSongUrl(unittest.TestCase):
    @patch("app.tools.netease_music.client.requests.post")
    def test_empty_url_raises_lookup(self, mock_post):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {"data": [{"id": 1, "url": None}]}
        mock_post.return_value = resp
        with self.assertRaises(LookupError):
            client.fetch_song_url(1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m unittest tests.test_netease_music_client -v`  
Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 client**

`app/tools/netease_music/__init__.py` 可为空。

`client.py` 要点（完整实现时按此逻辑）：

```python
"""网易云音乐游客客户端（最小 weapi）。"""
from __future__ import annotations

import base64
import json
import os
import random
import string
from dataclasses import dataclass
from typing import Any, Dict, List

import requests
from Crypto is NOT used — use stdlib only:

# AES: use cryptography OR pure openssl via...
```

**重要：不要引入 `pycryptodome`。** 使用标准库实现 AES-128-CBC：

- 用 `from cryptography...` ❌ 也不要
- 正确做法：内联最小 AES（或使用已有纯 Python AES）。为保证可打包与零新依赖，在 `client.py` 内实现 weapi 所需的 AES-128-CBC + PKCS#7，基于标准库无现成 AES，因此：

**依赖决策（本任务锁定）：** 新增 `pycryptodome` 到 `requirements.txt`（体积小、打包成熟）。若坚持零新依赖，改用手工移植的极简 AES——优先 **pycryptodome**，与 PyInstaller 兼容好。

更新 `requirements.txt` 增加一行：`pycryptodome>=3.20.0`

weapi 常量与流程（与 Binaryify / api-enhanced 一致）：

```python
_BASE = "https://music.163.com"
_PRESET_KEY = b"0CoJUm6Qyw8W8jud"
_IV = b"0102030405060708"
_PUBLIC_KEY = (
    "-----BEGIN PUBLIC KEY-----\n"
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDgtQn2JZ34ZC28NWYpAUd98iZ37BUrX/aKzmFbt7clFSs6sXq"
    "HauqKWqdtLkF2KexO40H1YTX8z2lSgBBOAxLsvaklV8k4cBFK9snQXE9/DDaFt6Rr7iVZMlg8jOhgK8Au3"
    "jJ7YryyCg1YhHHjn7DQIDAQAB\n-----END PUBLIC KEY-----"
)
# 实际实现：使用固定 modulus/exponent 十六进制做 RSA（与网易云常见实现相同），避免 PEM 解析依赖。
_MODULUS = (
    "00e0b509f6259fc8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a87aa"
    "aa2a5aa76d2e4176287c4e3e0d75d317f3cfa55a80513e0312ecbda4a955f24e1c0452bdba74171"
    "3dfc30da16de91afb89564c960f233a180af00bb78c9ed8af2c828356211c78e7ec340"
)
_PUB_EXP = int("010001", 16)

PAGE_SIZE = 30
HOT_PLAYLIST_ID = 3778678
NEW_PLAYLIST_ID = 3779629

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class SongItem:
    id: int
    name: str
    artists: str
    duration_ms: int


@dataclass
class SongPage:
    songs: List[SongItem]
    total: int
    page: int
    page_size: int


def _pad(data: bytes) -> bytes:
    pad = 16 - len(data) % 16
    return data + bytes([pad] * pad)


def _aes_encrypt(text: str, key: bytes) -> str:
    from Crypto.Cipher import AES

    cipher = AES.new(key, AES.MODE_CBC, _IV)
    encrypted = cipher.encrypt(_pad(text.encode("utf-8")))
    return base64.b64encode(encrypted).decode("utf-8")


def _rsa_encrypt(message: str) -> str:
    # message is 16-char secret key, reversed then RSA
    msg = message[::-1].encode("utf-8")
    m = int.from_bytes(msg, "big")
    c = pow(m, _PUB_EXP, int(_MODULUS, 16))
    return format(c, "x").zfill(256)


def _weapi_encrypt(data: Dict[str, Any]) -> Dict[str, str]:
    text = json.dumps(data, separators=(",", ":"))
    secret = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    params = _aes_encrypt(_aes_encrypt(text, _PRESET_KEY), secret.encode("utf-8"))
    enc_sec_key = _rsa_encrypt(secret)
    return {"params": params, "encSecKey": enc_sec_key}


def _headers() -> Dict[str, str]:
    return {
        "User-Agent": USER_AGENT,
        "Referer": "https://music.163.com/",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def _post_weapi(path: str, data: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    url = f"{_BASE}{path}"
    resp = requests.post(url, data=_weapi_encrypt(data), headers=_headers(), timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _artists_str(artists: List[Dict[str, Any]]) -> str:
    return "/".join(a.get("name", "") for a in artists if a.get("name"))


def _song_from_track(track: Dict[str, Any]) -> SongItem:
    artists = track.get("ar") or track.get("artists") or []
    return SongItem(
        id=int(track["id"]),
        name=str(track.get("name") or ""),
        artists=_artists_str(artists),
        duration_ms=int(track.get("dt") or track.get("duration") or 0),
    )


def _slice_page(songs: List[SongItem], page: int, page_size: int, total: int) -> SongPage:
    page = max(1, page)
    start = (page - 1) * page_size
    end = start + page_size
    return SongPage(songs=songs[start:end], total=total, page=page, page_size=page_size)


def fetch_playlist_songs(playlist_id: int, page: int = 1, timeout: int = 30) -> SongPage:
    data = _post_weapi(
        "/weapi/v3/playlist/detail",
        {"id": playlist_id, "n": 1000, "s": 0},
        timeout,
    )
    playlist = data.get("playlist") or {}
    tracks = playlist.get("tracks") or []
    songs = [_song_from_track(t) for t in tracks]
    total = int(playlist.get("trackCount") or len(songs))
    return _slice_page(songs, page, PAGE_SIZE, total)


def search_songs(keyword: str, page: int = 1, timeout: int = 30) -> SongPage:
    kw = keyword.strip()
    if not kw:
        raise ValueError("请输入搜索关键词")
    page = max(1, page)
    offset = (page - 1) * PAGE_SIZE
    data = _post_weapi(
        "/weapi/cloudsearch/pc",
        {"s": kw, "type": 1, "limit": PAGE_SIZE, "offset": offset, "total": True},
        timeout,
    )
    result = data.get("result") or {}
    songs_raw = result.get("songs") or []
    songs = [_song_from_track(t) for t in songs_raw]
    total = int(result.get("songCount") or len(songs))
    return SongPage(songs=songs, total=total, page=page, page_size=PAGE_SIZE)


def fetch_song_url(song_id: int, timeout: int = 30) -> str:
    data = _post_weapi(
        "/weapi/song/enhance/player/url/v1",
        {"ids": [song_id], "level": "standard", "encodeType": "mp3"},
        timeout,
    )
    items = data.get("data") or []
    if not items:
        raise LookupError("暂无法播放")
    url = items[0].get("url")
    if not url:
        raise LookupError("暂无法播放")
    return str(url)
```

注意：RSA modulus 字符串必须是网易云公开实现中的完整 hex（实现时从 Binaryify `util/crypto.js` 或 api-enhanced 同文件一字不差复制，上面示例可能被换行截断——**实现时核对长度为 256 hex chars after removing whitespace**）。

- [ ] **Step 4: 跑单测通过**

Run: `python -m pip install pycryptodome -i https://pypi.tuna.tsinghua.edu.cn/simple`  
Run: `python -m unittest tests.test_netease_music_client -v`  
Expected: PASS

可选手工：

```python
from app.tools.netease_music.client import fetch_playlist_songs, HOT_PLAYLIST_ID
print(fetch_playlist_songs(HOT_PLAYLIST_ID, page=1).songs[:2])
```

- [ ] **Step 5: Commit**

```bash
git add requirements.txt app/tools/netease_music/__init__.py app/tools/netease_music/client.py tests/test_netease_music_client.py
git commit -m "feat: add NetEase weapi client for guest music"
```

---

### Task 2: Worker 后台线程

**Files:**
- Create: `app/tools/netease_music/worker.py`

**Interfaces:**
- Consumes: `fetch_playlist_songs`, `search_songs`, `fetch_song_url`, `SongPage`
- Produces:
  - `class NeteaseWorker(QThread)` with signals `finished(object)`, `failed(str)`
  - 构造：`NeteaseWorker(kind: str, **kwargs)`  
    - `kind="playlist"` → `playlist_id`, `page`  
    - `kind="search"` → `keyword`, `page`  
    - `kind="url"` → `song_id`  
  - 成功时 `finished` 发射 `SongPage` 或 `str`（URL）

- [ ] **Step 1: 实现 worker（对齐 aihot_news/worker.py）**

```python
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
```

- [ ] **Step 2: 冒烟（可选）** — 在 Python REPL 中启动 QCoreApplication 跑一次 playlist worker，或跳过等 Task 4 联调。

- [ ] **Step 3: Commit**

```bash
git add app/tools/netease_music/worker.py
git commit -m "feat: add NetEase music background worker"
```

---

### Task 3: Player 封装

**Files:**
- Create: `app/tools/netease_music/player.py`

**Interfaces:**
- Produces: `class MusicPlayer(QObject)`
  - signals: `position_changed(int)`, `duration_changed(int)`, `state_changed(str)`, `error_occurred(str)`, `current_changed(object)`（`SongItem|None`）
  - `set_queue(songs: list[SongItem], start_index: int = 0) -> None`
  - `play_url(url: str, song: SongItem | None = None) -> None`
  - `toggle_play() -> None`
  - `play_next() -> None` / `play_prev() -> None`
  - `seek(ms: int) -> None`
  - `set_volume(0-100) -> None`
  - `current_index() -> int`
  - `queue() -> list[SongItem]`

- [ ] **Step 1: 实现 player.py**

```python
"""基于 QMediaPlayer 的播放封装。"""
from __future__ import annotations

from typing import List, Optional

from PyQt5.QtCore import QObject, QUrl, pyqtSignal
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer

from app.tools.netease_music.client import SongItem


class MusicPlayer(QObject):
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    state_changed = pyqtSignal(str)  # playing | paused | stopped
    error_occurred = pyqtSignal(str)
    current_changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer(self)
        self._queue: List[SongItem] = []
        self._index = -1
        self._player.positionChanged.connect(self.position_changed.emit)
        self._player.durationChanged.connect(self.duration_changed.emit)
        self._player.stateChanged.connect(self._on_state)
        self._player.error.connect(self._on_error)
        self._player.setVolume(50)

    def queue(self) -> List[SongItem]:
        return list(self._queue)

    def current_index(self) -> int:
        return self._index

    def set_queue(self, songs: List[SongItem], start_index: int = 0) -> None:
        self._queue = list(songs)
        self._index = start_index if songs else -1

    def play_url(self, url: str, song: Optional[SongItem] = None) -> None:
        if song is not None:
            self.current_changed.emit(song)
        self._player.setMedia(QMediaContent(QUrl(url)))
        self._player.play()

    def toggle_play(self) -> None:
        if self._player.state() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def play_next(self) -> Optional[SongItem]:
        if not self._queue or self._index < 0:
            return None
        if self._index + 1 >= len(self._queue):
            return None
        self._index += 1
        song = self._queue[self._index]
        self.current_changed.emit(song)
        return song

    def play_prev(self) -> Optional[SongItem]:
        if not self._queue or self._index <= 0:
            return None
        self._index -= 1
        song = self._queue[self._index]
        self.current_changed.emit(song)
        return song

    def seek(self, ms: int) -> None:
        self._player.setPosition(ms)

    def set_volume(self, value: int) -> None:
        self._player.setVolume(max(0, min(100, value)))

    def _on_state(self, state) -> None:
        mapping = {
            QMediaPlayer.PlayingState: "playing",
            QMediaPlayer.PausedState: "paused",
            QMediaPlayer.StoppedState: "stopped",
        }
        self.state_changed.emit(mapping.get(state, "stopped"))

    def _on_error(self, *_args) -> None:
        self.error_occurred.emit(self._player.errorString() or "播放失败")
```

- [ ] **Step 2: Commit**

```bash
git add app/tools/netease_music/player.py
git commit -m "feat: add QMediaPlayer wrapper for NetEase tool"
```

---

### Task 4: Widget UI + 注册 + README

**Files:**
- Create: `app/tools/netease_music/widget.py`
- Modify: `app/tools/registry.py`
- Modify: `README.md`（功能概览表增加一行）

**Interfaces:**
- Consumes: `NeteaseWorker`, `MusicPlayer`, `SongPage`, `SongItem`, `HOT_PLAYLIST_ID`, `NEW_PLAYLIST_ID`, `PAGE_SIZE`
- Produces: `class NeteaseMusicWidget(BaseToolWidget)` with `tool_id="netease_music"`, `tool_name="网易云听歌"`

- [ ] **Step 1: 实现 widget.py**

关键行为：

1. `QTabWidget`：热歌榜 / 新歌榜 / 搜索  
2. 搜索区仅在搜索 Tab 显示  
3. `QTableWidget` 或 `QListWidget` 展示歌名/歌手/时长；双击播放  
4. 分页：上一页 / `第 n 页` / 下一页；`total` 计算最大页  
5. `_request_seq` 计数：每次发起 Worker 自增；`finished` 回调比对序号，过期忽略  
6. 播放：先 `kind=url` Worker → 成功则 `player.set_queue(current_page_songs, index)` + `play_url`  
7. 上一首/下一首：`play_prev/next` 返回 `SongItem` 后再拉 URL  
8. 状态栏：`QLabel#statusInfo`  
9. 顶栏说明版权与游客限制  

骨架（实现时补全布局与样式 objectName，对齐其它工具）：

```python
class NeteaseMusicWidget(BaseToolWidget):
    tool_id = "netease_music"
    tool_name = "网易云听歌"

    def get_title(self) -> str:
        return self.tool_name

    # _load_playlist / _load_search / _on_page_result / _play_at
    # _start_worker(kind, **kwargs) 管理 self._worker 与 self._req_id
```

时长显示：`duration_ms // 1000` → `mm:ss`。

- [ ] **Step 2: 注册**

在 `registry.py`：

```python
from app.tools.netease_music.widget import NeteaseMusicWidget
# _TOOLS 列表加入 NeteaseMusicWidget（建议放在 AIHOT 之后或末尾）
```

- [ ] **Step 3: 更新 README 功能表**

增加一行：`| **网易云听歌** | 游客模式浏览热歌/新歌榜与搜索，应用内播放（学习测试用途） |`

- [ ] **Step 4: 手工验收**

Run: `python main.py`

核对规格验收标准：

1. 侧栏有「网易云听歌」，热歌/新歌可翻页  
2. 搜索有结果且可翻页  
3. 点歌可播、暂停、进度、音量  
4. 无登录；失败有提示  

若 Windows 无解码器导致 MP3 失败：状态栏显示播放失败；在 `docs/使用与打包指南.md` 简短注明「需系统可用的音频解码（Windows Media Feature Pack）」——仅当验收踩到再写。

- [ ] **Step 5: Commit**

```bash
git add app/tools/netease_music/widget.py app/tools/registry.py README.md
git commit -m "feat: add NetEase music listening tool UI"
```

---

## Spec Coverage Checklist

| 规格项 | 任务 |
|--------|------|
| 游客 weapi client | Task 1 |
| 热歌/新歌分页 | Task 1 + 4 |
| 搜索分页 | Task 1 + 4 |
| 播放 URL | Task 1 + 4 |
| QMediaPlayer 控制 | Task 3 + 4 |
| Worker 防卡顿 / 防串台 | Task 2 + 4（req id） |
| 错误提示 | Task 2 + 4 |
| 注册 + README | Task 4 |
| 不下载、无登录 | 全局约束，实现中遵守 |

---

## Self-Review Notes

- RSA modulus 必须以官方开源实现完整 hex 为准，计划中的换行示例不可直接截断使用。
- 榜单接口一次拉 tracks 后本地 `_slice_page`；搜索用服务端 offset。
- `pycryptodome` 为唯一新依赖，需写入 `requirements.txt` 并在打包环境安装。
