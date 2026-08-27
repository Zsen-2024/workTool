"""AIHOT 公开 API 客户端。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from app.tools.aihot_news.formatter import format_response

BASE_URL = "https://aihot.virxact.com"
USER_AGENT = "WorkTool/1.0 (+https://aihot.virxact.com/)"

ENDPOINTS = {
    "items_selected": "精选资讯",
    "items_all": "全部 AI 动态",
    "hot_topics": "当前热点榜",
    "daily_latest": "最新 AI 日报",
    "daily_index": "日报日期列表",
    "daily_by_date": "指定日期日报",
    "story": "事件详情",
}

CATEGORIES = {
    "": "全部分类",
    "ai-models": "模型",
    "ai-products": "产品",
    "industry": "行业",
    "paper": "论文",
    "tip": "观点/技巧",
}


@dataclass
class AihotRequest:
    endpoint: str
    window: str = "24h"
    limit: int = 20
    category: str = ""
    keyword: str = ""
    date: str = ""
    public_id: str = ""
    story_url: str = ""


@dataclass
class AihotResponse:
    url: str
    data: Dict[str, Any]
    formatted: str = ""


def _headers() -> Dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _extract_story_id(story_url: str) -> Optional[str]:
    url = story_url.strip().rstrip("/")
    prefix = "https://aihot.virxact.com/story/"
    if url.startswith(prefix):
        public_id = url[len(prefix) :]
        return public_id or None
    if "/" not in url and url:
        return url
    return None


def build_url(req: AihotRequest) -> str:
    if req.endpoint == "items_selected":
        params = {
            "mode": "selected",
            "window": req.window,
            "limit": req.limit,
            "by": "timeline",
        }
        if req.category:
            params["category"] = req.category
        if req.keyword.strip():
            params["q"] = req.keyword.strip()
        return f"{BASE_URL}/api/v1/items?{urlencode(params)}"

    if req.endpoint == "items_all":
        params = {
            "mode": "all",
            "window": req.window,
            "limit": req.limit,
            "by": "timeline",
        }
        if req.category:
            params["category"] = req.category
        if req.keyword.strip():
            params["q"] = req.keyword.strip()
        return f"{BASE_URL}/api/v1/items?{urlencode(params)}"

    if req.endpoint == "hot_topics":
        return f"{BASE_URL}/api/v1/hot-topics"

    if req.endpoint == "daily_latest":
        return f"{BASE_URL}/api/v1/dailies/latest"

    if req.endpoint == "daily_index":
        return f"{BASE_URL}/api/v1/dailies?{urlencode({'limit': req.limit})}"

    if req.endpoint == "daily_by_date":
        date = req.date.strip()
        if not date:
            raise ValueError("请输入日期，格式 YYYY-MM-DD")
        return f"{BASE_URL}/api/v1/dailies/{date}"

    if req.endpoint == "story":
        public_id = req.public_id.strip()
        if not public_id and req.story_url.strip():
            public_id = _extract_story_id(req.story_url) or ""
        if not public_id:
            raise ValueError("请输入事件 publicId 或热点事件链接")
        return f"{BASE_URL}/api/v1/stories/{public_id}"

    raise ValueError(f"未知接口类型：{req.endpoint}")


def fetch(req: AihotRequest, timeout: int = 30) -> AihotResponse:
    url = build_url(req)
    response = requests.get(url, headers=_headers(), timeout=timeout)
    response.raise_for_status()
    data = response.json()
    formatted = format_response(req.endpoint, data)
    return AihotResponse(url=url, data=data, formatted=formatted)
