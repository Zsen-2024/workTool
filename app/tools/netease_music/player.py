"""基于 QMediaPlayer 的播放封装。"""

from __future__ import annotations

from typing import List, Optional

from PyQt5.QtCore import QObject, QUrl, pyqtSignal
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer

from app.tools.netease_music.client import SongItem


class MusicPlayer(QObject):
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    state_changed = pyqtSignal(str)
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
