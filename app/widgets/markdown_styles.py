"""Markdown 展示样式与渲染。"""

from __future__ import annotations

from PyQt5.QtWidgets import QTextBrowser

MARKDOWN_STYLE = """
body { font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif; color: #1F2329; line-height: 1.6; }
h1 { font-size: 26px; font-weight: 600; margin: 0 0 16px 0; color: #1F2329; }
h2 { font-size: 22px; font-weight: 600; margin: 0 0 14px 0; color: #1F2329; }
h3 { font-size: 17px; font-weight: 600; margin: 20px 0 10px 0; color: #1F2329; }
p { margin: 8px 0; }
ul, ol { margin: 8px 0 14px 0; padding-left: 22px; }
li { margin: 6px 0; }
blockquote { margin: 10px 0; padding: 10px 14px; border-left: 3px solid #1677FF;
             background: #F7F8FA; color: #4E5969; border-radius: 0 6px 6px 0; }
a { color: #1677FF; text-decoration: none; }
a:hover { text-decoration: underline; }
hr { border: none; border-top: 1px solid #E5E6EB; margin: 18px 0; }
code { background: #F2F3F5; color: #1677FF; padding: 1px 6px; border-radius: 4px; font-family: Consolas, monospace; }
pre { margin: 12px 0; padding: 12px 14px; background: #F7F8FA; border: 1px solid #E5E6EB;
      border-radius: 6px; overflow-x: auto; }
pre code { background: transparent; color: #1F2329; padding: 0; }
em { color: #86909C; }
table { border-collapse: collapse; width: 100%; margin: 14px 0 18px 0;
        border: 1px solid #E5E6EB; background: #FFFFFF; }
td, th { border: 1px solid #E5E6EB; padding: 10px 14px; vertical-align: top; line-height: 1.55; }
td p, th p { margin: 0; }
tr:nth-child(even) td { background: #FAFBFC; }
tr:first-child td { background: #F7F8FA; color: #1F2329; }
"""

_TABLE_ATTRS = 'border="1" cellspacing="2"'
_TABLE_ATTRS_FIXED = 'cellspacing="0" cellpadding="0"'


def configure_markdown_view(view: QTextBrowser) -> None:
    """为 Markdown 视图应用统一样式表。"""
    view.document().setDefaultStyleSheet(MARKDOWN_STYLE)


def set_markdown_content(view: QTextBrowser, text: str) -> None:
    """渲染 Markdown 并优化表格等 Qt 默认 HTML 表现。"""
    view.setMarkdown(text)
    html = view.toHtml()
    if _TABLE_ATTRS in html:
        html = html.replace(_TABLE_ATTRS, _TABLE_ATTRS_FIXED)
        view.setHtml(html)
