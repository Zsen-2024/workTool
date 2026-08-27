"""生成 WorkTool 应用图标（assets/icon.ico）。"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "icon.ico"

PRIMARY = (22, 119, 255)  # #1677FF
PRIMARY_DARK = (9, 88, 217)  # #0958D9
WHITE = (255, 255, 255)


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _rounded_rect(draw: ImageDraw.ImageDraw, box: tuple, radius: int, fill) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def _draw_wrench(draw: ImageDraw.ImageDraw, size: int) -> None:
    cx, cy = size // 2, size // 2
    scale = size / 256

    # 工具箱主体
    box_w, box_h = int(118 * scale), int(88 * scale)
    left = cx - box_w // 2
    top = cy - int(8 * scale)
    _rounded_rect(draw, (left, top, left + box_w, top + box_h), int(14 * scale), WHITE)

    # 工具箱把手
    handle_w, handle_h = int(52 * scale), int(16 * scale)
    hx = cx - handle_w // 2
    hy = top - handle_h + int(4 * scale)
    _rounded_rect(draw, (hx, hy, hx + handle_w, hy + handle_h), int(8 * scale), WHITE)

    # 中间分隔线
    mid_y = top + int(36 * scale)
    draw.line(
        (left + int(18 * scale), mid_y, left + box_w - int(18 * scale), mid_y),
        fill=PRIMARY,
        width=max(2, int(6 * scale)),
    )

    # 左侧扳手简形
    wx = left + int(34 * scale)
    wy = mid_y + int(18 * scale)
    r = int(14 * scale)
    draw.ellipse((wx - r, wy - r, wx + r, wy + r), outline=PRIMARY, width=max(2, int(5 * scale)))
    draw.line(
        (wx + r - int(2 * scale), wy, wx + int(34 * scale), wy - int(22 * scale)),
        fill=PRIMARY,
        width=max(2, int(5 * scale)),
    )

    # 右侧 "{}" 象征 JSON 工具
    brace_x = left + box_w - int(52 * scale)
    brace_y = mid_y + int(12 * scale)
    fs = max(10, int(28 * scale))
    draw.text((brace_x, brace_y), "{}", fill=PRIMARY)


def render_icon(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin = max(2, size // 16)
    for y in range(size):
        t = y / max(size - 1, 1)
        color = (
            _lerp(PRIMARY[0], PRIMARY_DARK[0], t),
            _lerp(PRIMARY[1], PRIMARY_DARK[1], t),
            _lerp(PRIMARY[2], PRIMARY_DARK[2], t),
            255,
        )
        draw.line((margin, y, size - margin, y), fill=color)

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 5, fill=255)
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(size):
        t = y / max(size - 1, 1)
        color = (
            _lerp(PRIMARY[0], PRIMARY_DARK[0], t),
            _lerp(PRIMARY[1], PRIMARY_DARK[1], t),
            _lerp(PRIMARY[2], PRIMARY_DARK[2], t),
            255,
        )
        bg_draw.line((0, y, size, y), fill=color)
    bg.putalpha(mask)
    image = bg

    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    _draw_wrench(overlay_draw, size)
    return Image.alpha_composite(image, overlay)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    sizes = (16, 24, 32, 48, 64, 128, 256)
    images = [render_icon(s) for s in sizes]
    images[0].save(
        OUTPUT,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"Icon saved: {OUTPUT}")


if __name__ == "__main__":
    main()
