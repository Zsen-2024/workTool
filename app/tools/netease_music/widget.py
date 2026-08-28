"""网易云听歌工具界面。"""

from __future__ import annotations

import math
from typing import List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.tools.base import BaseToolWidget
from app.tools.netease_music.client import (
    HOT_PLAYLIST_ID,
    NEW_PLAYLIST_ID,
    PAGE_SIZE,
    SongItem,
    SongPage,
)
from app.tools.netease_music.player import MusicPlayer
from app.tools.netease_music.worker import NeteaseWorker


def _format_ms(ms: int) -> str:
    total = max(0, int(ms) // 1000)
    return f"{total // 60:02d}:{total % 60:02d}"


class NeteaseMusicWidget(BaseToolWidget):
    tool_id = "netease_music"
    tool_name = "网易云听歌"

    def get_title(self) -> str:
        return self.tool_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._list_worker: Optional[NeteaseWorker] = None
        self._url_worker: Optional[NeteaseWorker] = None
        self._list_req_id = 0
        self._url_req_id = 0
        self._page = 1
        self._total = 0
        self._songs: List[SongItem] = []
        self._seeking = False
        self._player = MusicPlayer(self)
        self._build_ui()
        self._wire_player()
        self._tabs.currentChanged.connect(self._on_tab_changed)
        self._on_tab_changed(0)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel(self.get_title())
        title.setObjectName("toolTitle")
        layout.addWidget(title)

        hint = QLabel(
            "游客模式 · 仅供个人学习测试，版权归网易云所有；"
            "可播免费/试听内容，无版权或仅 VIP 曲目会提示暂无法播放。"
        )
        hint.setObjectName("statusInfo")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("httpTabs")
        self._tabs.addTab(QWidget(), "热歌榜")
        self._tabs.addTab(QWidget(), "新歌榜")
        self._tabs.addTab(QWidget(), "搜索")
        layout.addWidget(self._tabs)

        search_row = QHBoxLayout()
        self._keyword = QLineEdit()
        self._keyword.setPlaceholderText("输入歌名 / 歌手关键词…")
        self._keyword.returnPressed.connect(self._do_search)
        self._btn_search = QPushButton("搜索")
        self._btn_search.setObjectName("primaryButton")
        self._btn_search.setFixedWidth(88)
        self._btn_search.clicked.connect(self._do_search)
        search_row.addWidget(self._keyword, 1)
        search_row.addWidget(self._btn_search)
        layout.addLayout(search_row)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["#", "歌名", "歌手", "时长"])
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.doubleClicked.connect(lambda *_: self._play_selected())
        layout.addWidget(self._table, 1)

        page_row = QHBoxLayout()
        self._btn_prev = QPushButton("上一页")
        self._btn_prev.clicked.connect(self._prev_page)
        self._page_label = QLabel("第 1 页")
        self._btn_next = QPushButton("下一页")
        self._btn_next.clicked.connect(self._next_page)
        self._btn_play = QPushButton("播放选中")
        self._btn_play.setObjectName("primaryButton")
        self._btn_play.clicked.connect(self._play_selected)
        page_row.addWidget(self._btn_prev)
        page_row.addWidget(self._page_label)
        page_row.addWidget(self._btn_next)
        page_row.addStretch(1)
        page_row.addWidget(self._btn_play)
        layout.addLayout(page_row)

        self._status = QLabel("就绪")
        self._status.setObjectName("statusInfo")
        layout.addWidget(self._status)
        layout.addWidget(self._build_player_bar())

    def _build_player_bar(self) -> QWidget:
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 8, 0, 0)
        row.setSpacing(8)

        self._btn_prev_track = QPushButton("上一首")
        self._btn_prev_track.clicked.connect(self._play_prev)
        self._btn_toggle = QPushButton("播放")
        self._btn_toggle.setObjectName("primaryButton")
        self._btn_toggle.clicked.connect(self._player.toggle_play)
        self._btn_next_track = QPushButton("下一首")
        self._btn_next_track.clicked.connect(self._play_next)
        row.addWidget(self._btn_prev_track)
        row.addWidget(self._btn_toggle)
        row.addWidget(self._btn_next_track)

        self._now_playing = QLabel("未播放")
        self._now_playing.setMinimumWidth(140)
        row.addWidget(self._now_playing, 1)

        self._pos_label = QLabel("00:00")
        self._progress = QSlider(Qt.Horizontal)
        self._progress.setRange(0, 0)
        self._progress.sliderPressed.connect(self._on_seek_pressed)
        self._progress.sliderReleased.connect(self._on_seek_released)
        self._dur_label = QLabel("00:00")
        row.addWidget(self._pos_label)
        row.addWidget(self._progress, 2)
        row.addWidget(self._dur_label)

        row.addWidget(QLabel("音量"))
        self._volume = QSlider(Qt.Horizontal)
        self._volume.setRange(0, 100)
        self._volume.setValue(50)
        self._volume.setFixedWidth(100)
        self._volume.valueChanged.connect(self._player.set_volume)
        row.addWidget(self._volume)
        return bar

    def _wire_player(self) -> None:
        self._player.position_changed.connect(self._on_position)
        self._player.duration_changed.connect(self._on_duration)
        self._player.state_changed.connect(self._on_state)
        self._player.error_occurred.connect(lambda msg: self._set_status(msg, error=True))
        self._player.current_changed.connect(self._on_current)

    def _set_status(self, message: str, error: bool = False) -> None:
        self._status.setObjectName("statusError" if error else "statusInfo")
        self._status.setText(message)
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

    def _max_page(self) -> int:
        if self._total <= 0:
            return 1
        return max(1, math.ceil(self._total / PAGE_SIZE))

    def _update_pager(self) -> None:
        if self._total:
            self._page_label.setText(
                f"第 {self._page} / {self._max_page()} 页（共 {self._total} 首）"
            )
        else:
            self._page_label.setText(f"第 {self._page} 页")
        self._btn_prev.setEnabled(self._page > 1)
        self._btn_next.setEnabled(self._page < self._max_page() if self._total else True)

    def _tab_key(self) -> str:
        idx = self._tabs.currentIndex()
        if idx == 0:
            return "hot"
        if idx == 1:
            return "new"
        return "search"

    def _on_tab_changed(self, _index: int) -> None:
        is_search = self._tab_key() == "search"
        self._keyword.setVisible(is_search)
        self._btn_search.setVisible(is_search)
        self._page = 1
        if is_search:
            self._songs = []
            self._total = 0
            self._fill_table([])
            self._update_pager()
            self._set_status("输入关键词后搜索")
        else:
            self._load_list()

    def _do_search(self) -> None:
        self._page = 1
        self._load_list()

    def _prev_page(self) -> None:
        if self._page <= 1:
            return
        self._page -= 1
        self._load_list()

    def _next_page(self) -> None:
        if self._total and self._page >= self._max_page():
            return
        self._page += 1
        self._load_list()

    def _load_list(self) -> None:
        key = self._tab_key()
        if key == "search":
            keyword = self._keyword.text().strip()
            if not keyword:
                self._set_status("请输入搜索关键词", error=True)
                return
            self._start_list_worker("search", keyword=keyword, page=self._page)
        elif key == "hot":
            self._start_list_worker(
                "playlist", playlist_id=HOT_PLAYLIST_ID, page=self._page
            )
        else:
            self._start_list_worker(
                "playlist", playlist_id=NEW_PLAYLIST_ID, page=self._page
            )

    def _disconnect_worker(self, worker: Optional[NeteaseWorker]) -> None:
        if worker is None:
            return
        try:
            worker.finished.disconnect()
        except TypeError:
            pass
        try:
            worker.failed.disconnect()
        except TypeError:
            pass

    def _start_list_worker(self, kind: str, **kwargs) -> None:
        self._list_req_id += 1
        req_id = self._list_req_id
        self._set_status("加载中…")
        self._btn_prev.setEnabled(False)
        self._btn_next.setEnabled(False)
        self._disconnect_worker(self._list_worker)
        self._list_worker = NeteaseWorker(kind, **kwargs)
        self._list_worker.finished.connect(
            lambda result, rid=req_id: self._on_list_ok(result, rid)
        )
        self._list_worker.failed.connect(
            lambda msg, rid=req_id: self._on_list_fail(msg, rid)
        )
        self._list_worker.start()

    def _on_list_ok(self, result: object, req_id: int) -> None:
        if req_id != self._list_req_id:
            return
        if not isinstance(result, SongPage):
            self._set_status("返回数据异常", error=True)
            return
        self._songs = list(result.songs)
        self._total = result.total
        self._page = result.page
        self._fill_table(self._songs)
        self._update_pager()
        self._set_status(f"已加载 {len(self._songs)} 首")

    def _on_list_fail(self, message: str, req_id: int) -> None:
        if req_id != self._list_req_id:
            return
        self._update_pager()
        self._set_status(message, error=True)

    def _fill_table(self, songs: List[SongItem]) -> None:
        self._table.setRowCount(len(songs))
        start = (self._page - 1) * PAGE_SIZE
        for row, song in enumerate(songs):
            values = [
                str(start + row + 1),
                song.name,
                song.artists,
                _format_ms(song.duration_ms),
            ]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                if col == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(row, col, item)

    def _selected_index(self) -> int:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return -1
        return rows[0].row()

    def _play_selected(self) -> None:
        idx = self._selected_index()
        if idx < 0 or idx >= len(self._songs):
            self._set_status("请先选择一首歌", error=True)
            return
        self._player.set_queue(self._songs, idx)
        self._request_play(self._songs[idx])

    def _play_next(self) -> None:
        song = self._player.play_next()
        if song is None:
            self._set_status("已经是列表最后一首")
            return
        self._request_play(song)

    def _play_prev(self) -> None:
        song = self._player.play_prev()
        if song is None:
            self._set_status("已经是列表第一首")
            return
        self._request_play(song)

    def _request_play(self, song: SongItem) -> None:
        self._url_req_id += 1
        req_id = self._url_req_id
        self._set_status(f"获取播放地址：{song.name} …")
        self._now_playing.setText(f"{song.name} - {song.artists}")
        self._disconnect_worker(self._url_worker)
        self._url_worker = NeteaseWorker("url", song_id=song.id)
        self._url_worker.finished.connect(
            lambda result, rid=req_id, s=song: self._on_url_ok(result, rid, s)
        )
        self._url_worker.failed.connect(
            lambda msg, rid=req_id: self._on_url_fail(msg, rid)
        )
        self._url_worker.start()

    def _on_url_ok(self, result: object, req_id: int, song: SongItem) -> None:
        if req_id != self._url_req_id:
            return
        if not isinstance(result, str) or not result:
            self._set_status("暂无法播放", error=True)
            return
        self._player.play_url(result, song)
        self._set_status(f"正在播放：{song.name}")

    def _on_url_fail(self, message: str, req_id: int) -> None:
        if req_id != self._url_req_id:
            return
        self._set_status(message or "暂无法播放", error=True)

    def _on_current(self, song: object) -> None:
        if isinstance(song, SongItem):
            self._now_playing.setText(f"{song.name} - {song.artists}")

    def _on_state(self, state: str) -> None:
        self._btn_toggle.setText("暂停" if state == "playing" else "播放")

    def _on_position(self, pos: int) -> None:
        self._pos_label.setText(_format_ms(pos))
        if not self._seeking:
            self._progress.setValue(pos)

    def _on_duration(self, dur: int) -> None:
        self._dur_label.setText(_format_ms(dur))
        self._progress.setRange(0, max(0, dur))

    def _on_seek_pressed(self) -> None:
        self._seeking = True

    def _on_seek_released(self) -> None:
        self._seeking = False
        self._player.seek(self._progress.value())
