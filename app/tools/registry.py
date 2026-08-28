from typing import List, Type

from app.tools.aihot_news.widget import AihotNewsWidget
from app.tools.base import BaseToolWidget
from app.tools.browser_search.widget import BrowserSearchWidget
from app.tools.http_client.widget import HttpClientWidget
from app.tools.json_formatter.widget import JsonFormatterWidget
from app.tools.markdown_preview.widget import MarkdownPreviewWidget
from app.tools.netease_music.widget import NeteaseMusicWidget

_TOOLS: List[Type[BaseToolWidget]] = [
    AihotNewsWidget,
    NeteaseMusicWidget,
    BrowserSearchWidget,
    HttpClientWidget,
    MarkdownPreviewWidget,
    JsonFormatterWidget,
]


def get_tools() -> List[Type[BaseToolWidget]]:
    return list(_TOOLS)
