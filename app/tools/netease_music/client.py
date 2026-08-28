"""网易云音乐游客客户端（最小 weapi）。"""

from __future__ import annotations

import base64
import json
import random
import string
from dataclasses import dataclass
from typing import Any, Dict, List

import requests
from Crypto.Cipher import AES

_BASE = "https://music.163.com"
_PRESET_KEY = b"0CoJUm6Qyw8W8jud"
_IV = b"0102030405060708"
_MODULUS = (
    "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725"
    "152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312"
    "ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424"
    "d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
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
    cipher = AES.new(key, AES.MODE_CBC, _IV)
    encrypted = cipher.encrypt(_pad(text.encode("utf-8")))
    return base64.b64encode(encrypted).decode("utf-8")


def _rsa_encrypt(message: str) -> str:
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
    resp = requests.post(
        url,
        data=_weapi_encrypt(data),
        headers=_headers(),
        timeout=timeout,
    )
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


def _slice_page(
    songs: List[SongItem],
    page: int,
    page_size: int,
    total: int,
) -> SongPage:
    page = max(1, page)
    start = (page - 1) * page_size
    end = start + page_size
    return SongPage(
        songs=songs[start:end],
        total=total,
        page=page,
        page_size=page_size,
    )


def fetch_playlist_songs(
    playlist_id: int,
    page: int = 1,
    timeout: int = 30,
) -> SongPage:
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
        {
            "s": kw,
            "type": 1,
            "limit": PAGE_SIZE,
            "offset": offset,
            "total": True,
        },
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
