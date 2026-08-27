"""读取 Chrome / Edge 浏览历史与书签。"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, List, Optional
from urllib.parse import urlparse

TZ_CN = timezone(timedelta(hours=8))

CHROME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


@dataclass
class BrowserEntry:
    title: str
    url: str
    source: str
    visited_at: str = ""


def _local_app_data() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", ""))


def _iter_chrome_profiles() -> Iterator[tuple[str, Path]]:
    root = _local_app_data() / "Google" / "Chrome" / "User Data"
    yield from _iter_profiles_in(root, "Chrome")


def _iter_edge_profiles() -> Iterator[tuple[str, Path]]:
    root = _local_app_data() / "Microsoft" / "Edge" / "User Data"
    yield from _iter_profiles_in(root, "Edge")


def _iter_profiles_in(root: Path, browser: str) -> Iterator[tuple[str, Path]]:
    if not root.is_dir():
        return
    local_state = root / "Local State"
    names = ["Default"]
    if local_state.is_file():
        try:
            data = json.loads(local_state.read_text(encoding="utf-8"))
            info_cache = data.get("profile", {}).get("info_cache", {})
            names = list(dict.fromkeys(names + list(info_cache.keys())))
        except (OSError, json.JSONDecodeError):
            pass
    for name in names:
        profile = root / name
        if profile.is_dir() and ((profile / "History").exists() or (profile / "Bookmarks").exists()):
            yield f"{browser} · {name}", profile


def _chrome_time_to_str(value: Optional[int]) -> str:
    if not value:
        return ""
    try:
        dt = CHROME_EPOCH + timedelta(microseconds=value)
        return dt.astimezone(TZ_CN).strftime("%Y-%m-%d %H:%M")
    except (OverflowError, ValueError):
        return ""


def _query_history(history_file: Path, keyword: str, limit: int) -> List[BrowserEntry]:
    if not history_file.is_file():
        return []
    tmp = Path(tempfile.gettempdir()) / f"worktool_hist_{history_file.stat().st_mtime_ns}.db"
    try:
        shutil.copy2(history_file, tmp)
    except OSError:
        return []

    entries: List[BrowserEntry] = []
    try:
        conn = sqlite3.connect(str(tmp))
        if keyword:
            pattern = f"%{keyword}%"
            cursor = conn.execute(
                """
                SELECT url, title, last_visit_time
                FROM urls
                WHERE hidden = 0 AND visit_count > 0
                  AND (title LIKE ? OR url LIKE ?)
                ORDER BY last_visit_time DESC
                LIMIT ?
                """,
                (pattern, pattern, limit),
            )
        else:
            cursor = conn.execute(
                """
                SELECT url, title, last_visit_time
                FROM urls
                WHERE hidden = 0 AND visit_count > 0
                ORDER BY last_visit_time DESC
                LIMIT ?
                """,
                (limit,),
            )
        for url, title, visited in cursor.fetchall():
            if not url or not str(url).startswith(("http://", "https://")):
                continue
            entries.append(
                BrowserEntry(
                    title=(title or url or "（无标题）").strip(),
                    url=str(url),
                    source="历史",
                    visited_at=_chrome_time_to_str(visited),
                )
            )
        conn.close()
    except sqlite3.Error:
        return []
    finally:
        tmp.unlink(missing_ok=True)
    return entries


def _walk_bookmarks(node: dict, keyword: str, results: List[BrowserEntry], limit: int) -> None:
    if len(results) >= limit:
        return
    node_type = node.get("type")
    if node_type == "url":
        url = node.get("url") or ""
        name = (node.get("name") or url or "（无标题）").strip()
        if not url.startswith(("http://", "https://")):
            return
        if keyword:
            key = keyword.lower()
            if key not in name.lower() and key not in url.lower():
                return
        results.append(BrowserEntry(title=name, url=url, source="书签"))
        return
    for child in node.get("children") or []:
        _walk_bookmarks(child, keyword, results, limit)


def _query_bookmarks(bookmarks_file: Path, keyword: str, limit: int) -> List[BrowserEntry]:
    if not bookmarks_file.is_file():
        return []
    try:
        data = json.loads(bookmarks_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    results: List[BrowserEntry] = []
    roots = data.get("roots") or {}
    for root in roots.values():
        _walk_bookmarks(root, keyword, results, limit)
        if len(results) >= limit:
            break
    return results[:limit]


def search_browser_data(
    keyword: str,
    scope: str = "all",
    kind: str = "all",
    limit: int = 80,
    *,
    browse_all: bool = False,
) -> List[BrowserEntry]:
    """检索浏览器历史与书签。scope: all/chrome/edge；kind: all/history/bookmark。"""
    keyword = keyword.strip()
    if not keyword and not browse_all:
        return []
    if browse_all and not keyword:
        limit = max(limit, 200)

    profile_iters: List[Iterator[tuple[str, Path]]] = []
    if scope in {"all", "chrome"}:
        profile_iters.append(_iter_chrome_profiles())
    if scope in {"all", "edge"}:
        profile_iters.append(_iter_edge_profiles())

    results: List[BrowserEntry] = []
    seen_urls = set()

    for profile_iter in profile_iters:
        for profile_name, profile_path in profile_iter:
            batch: List[BrowserEntry] = []
            if kind in {"all", "history"}:
                for item in _query_history(profile_path / "History", keyword, limit):
                    item.source = f"{profile_name} · 历史"
                    batch.append(item)
            if kind in {"all", "bookmark"}:
                for item in _query_bookmarks(profile_path / "Bookmarks", keyword, limit):
                    item.source = f"{profile_name} · 书签"
                    batch.append(item)

            for item in batch:
                key = item.url.rstrip("/")
                if key in seen_urls:
                    continue
                seen_urls.add(key)
                results.append(item)
                if len(results) >= limit:
                    return results
    return results


def open_url(url: str) -> bool:
    """在系统默认浏览器中打开 URL。"""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    import webbrowser

    return webbrowser.open(url)
