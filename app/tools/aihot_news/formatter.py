"""AIHOT 响应 Markdown 格式化。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

TZ_CN = timezone(timedelta(hours=8))

CATEGORY_LABELS = {
    "ai-models": "模型",
    "ai-products": "产品",
    "industry": "行业",
    "paper": "论文",
    "tip": "观点/技巧",
}


def fmt_time(iso: Optional[str]) -> str:
    if not iso:
        return "时间未知"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone(TZ_CN).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return iso


def _md_link(text: str, url: str) -> str:
    safe_text = text.replace("[", "\\[").replace("]", "\\]")
    return f"[{safe_text}]({url})" if url else safe_text


def _footer() -> str:
    return "\n---\n\n*数据来源：[AIHOT](https://aihot.virxact.com/)*"


def _format_items(data: Dict[str, Any]) -> str:
    query = data.get("query", {})
    items: List[Dict[str, Any]] = data.get("items", [])
    mode = "精选" if query.get("mode") == "selected" else "全部"
    category = CATEGORY_LABELS.get(query.get("category") or "", "全部")
    lines = [
        f"## AIHOT 资讯（共 {len(items)} 条）",
        "",
        f"> **模式**：{mode} · **时间窗**：{query.get('window', '-')} · **分类**：{category}",
        "",
    ]
    if not items:
        lines.append("*暂无匹配资讯。*")
        return "\n".join(lines) + _footer()

    for index, item in enumerate(items, 1):
        title = item.get("title") or "（无标题）"
        source = (item.get("source") or {}).get("name") or "未知来源"
        score = item.get("score")
        pub = fmt_time(item.get("publishedAt") or item.get("discoveredAt"))
        link = (item.get("links") or {}).get("aihot") or ""
        summary = (item.get("summary") or "").strip()
        reason = (item.get("reason") or "").strip()

        if link:
            heading = f"### {_md_link(title, link)}"
        else:
            heading = f"### {index}. {title}"
        if score is not None:
            heading += f"  `AI {score}`"
        lines.append(heading)
        lines.append("")
        lines.append(f"- **来源**：{source}")
        lines.append(f"- **时间**：{pub}")
        if summary:
            lines.append(f"- **摘要**：{summary}")
        if reason:
            lines.append(f"- **推荐理由**：{reason}")
        lines.append("")

    page = data.get("page") or {}
    if page.get("hasMore"):
        lines.append("*还有更多内容，可调大 limit 或使用 API cursor 翻页*")
    return "\n".join(lines) + _footer()


def _format_hot_topics(data: Dict[str, Any]) -> str:
    items: List[Dict[str, Any]] = data.get("items", [])
    lines = [f"## AIHOT 当前热点（共 {len(items)} 条）", ""]
    if not items:
        lines.append("*暂无热点数据。*")
        return "\n".join(lines) + _footer()

    for item in items:
        rank = item.get("rank", "?")
        title = item.get("title") or "（无标题）"
        source_count = item.get("sourceCount")
        latest = fmt_time(item.get("latestAt"))
        link = (item.get("links") or {}).get("aihot") or ""
        story = (item.get("links") or {}).get("story") or ""
        summary = (item.get("summary") or "").strip()

        lines.append(f"### 第 {rank} 名 · {_md_link(title, link) if link else title}")
        lines.append("")
        if source_count is not None:
            lines.append(f"- **报道信源**：{source_count} 家 · **最近更新**：{latest}")
        if summary:
            lines.append(f"- **摘要**：{summary}")
        links = []
        if link:
            links.append(_md_link("查看详情", link))
        if story:
            links.append(_md_link("事件页", story))
        if links:
            lines.append(f"- **链接**：{' · '.join(links)}")
        lines.append("")

    return "\n".join(lines) + _footer()


def _format_daily_index(data: Dict[str, Any]) -> str:
    items: List[Dict[str, Any]] = data.get("items", [])
    lines = [f"## AIHOT 日报索引（共 {len(items)} 个日期）", ""]
    for item in items:
        date = item.get("date") or "未知日期"
        title = item.get("title") or ""
        link = (item.get("links") or {}).get("aihot") or ""
        label = f"{date} · {title}".strip(" ·")
        lines.append(f"- {_md_link(label, link) if link else label}")
    return "\n".join(lines) + _footer()


def _format_daily_report(data: Dict[str, Any]) -> str:
    report = data.get("report") or {}
    date = report.get("date") or "未知日期"
    title = report.get("title") or "AI 日报"
    lead = (report.get("lead") or "").strip()
    lines = [f"## {title}", "", f"> **日期**：{date}", ""]
    if lead:
        lines.extend(["### 导语", "", lead, ""])

    for section in report.get("sections") or []:
        section_title = section.get("title") or "未命名板块"
        lines.extend([f"### {section_title}", ""])
        for flash in section.get("flashes") or []:
            flash_title = flash.get("title") or "（无标题）"
            summary = (flash.get("summary") or "").strip()
            link = (flash.get("links") or {}).get("original") or (flash.get("links") or {}).get("aihot") or ""
            lines.append(f"- {_md_link(flash_title, link) if link else flash_title}")
            if summary:
                lines.append(f"  \n  {summary}")
        lines.append("")

    return "\n".join(lines) + _footer()


def _format_story(data: Dict[str, Any]) -> str:
    story = data.get("story") or {}
    title = story.get("title") or "事件详情"
    status = story.get("status") or ""
    latest = (story.get("latest") or "").strip()
    digest = (story.get("digest") or "").strip()

    lines = [f"## {title}"]
    if status:
        lines.extend(["", f"> **状态**：{status}"])
    lines.append("")

    if latest:
        lines.extend(["### 最新进展", "", latest, ""])
    if digest:
        lines.extend(["### 事件综述", "", digest, ""])

    reports = story.get("reports") or []
    if reports:
        lines.extend(["### 报道时间线", ""])
        for report in reports:
            rep_title = report.get("title") or "（无标题）"
            rep_time = fmt_time(report.get("publishedAt") or report.get("discoveredAt"))
            source = (report.get("source") or {}).get("name") or "未知来源"
            link = (report.get("links") or {}).get("aihot") or ""
            label = f"**{rep_time}** · {rep_title}（{source}）"
            lines.append(f"- {_md_link(label, link) if link else label}")
        lines.append("")

    return "\n".join(lines) + _footer()


def format_response(endpoint: str, data: Dict[str, Any]) -> str:
    if endpoint in {"items_selected", "items_all"}:
        return _format_items(data)
    if endpoint == "hot_topics":
        return _format_hot_topics(data)
    if endpoint in {"daily_latest", "daily_by_date"}:
        return _format_daily_report(data)
    if endpoint == "daily_index":
        return _format_daily_index(data)
    if endpoint == "story":
        return _format_story(data)
    return ""
