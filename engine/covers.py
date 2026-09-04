from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1440
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")

PALETTES = [
    ("stamp", "#FF5A36", "#141412", "#F2EFDF"),
    ("paper", "#F2EFDF", "#141412", "#FF5A36"),
    ("ink", "#141412", "#F2EFDF", "#D8FF3E"),
    ("index", "#D8FF3E", "#141412", "#FF5A36"),
]


def _font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold and FONT_BOLD.exists() else FONT_REGULAR
    return ImageFont.truetype(str(path), size, encoding="unic")


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for ch in text.replace("\n", ""):
        trial = line + ch
        if font.getlength(trial) <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = ch
    if line:
        lines.append(line)
    return lines[:5] or [text[:8]]


def _draw_title(draw: ImageDraw.ImageDraw, title: str, font: ImageFont.FreeTypeFont, fill: str, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    lines = wrap_text(title, font, x1 - x0)
    line_h = int(font.size * 1.18)
    total = line_h * len(lines)
    y = y0 + max(0, (y1 - y0 - total) // 2)
    for line in lines:
        w = font.getlength(line)
        x = x0 + max(0, (x1 - x0 - w) // 2)
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h


def render_cover(title: str, topic: str, style: str, fg: str, bg: str, accent: str) -> bytes:
    img = Image.new("RGB", (WIDTH, HEIGHT), bg)
    draw = ImageDraw.Draw(img)
    title_font = _font(True, 96)
    meta_font = _font(False, 36)

    if style == "stamp":
        draw.rectangle((72, 72, WIDTH - 72, HEIGHT - 72), outline=fg, width=10)
        draw.rectangle((72, 72, 280, 160), fill=accent)
        draw.text((92, 92), "COVER", font=meta_font, fill=fg)
        _draw_title(draw, title, title_font, fg, (90, 280, WIDTH - 90, 1080))
        draw.text((90, 1260), topic[:16], font=meta_font, fill=fg)
    elif style == "paper":
        draw.rectangle((0, 0, WIDTH, 28), fill=accent)
        _draw_title(draw, title, title_font, fg, (80, 240, WIDTH - 80, 1100))
        draw.rectangle((80, 1220, 360, 1288), fill=accent)
        draw.text((96, 1232), "草稿封面", font=meta_font, fill=fg)
    elif style == "ink":
        draw.ellipse((680, -120, 1280, 480), fill=accent)
        _draw_title(draw, title, title_font, fg, (80, 360, WIDTH - 80, 1120))
        draw.text((80, 1280), topic[:16], font=meta_font, fill=accent)
    else:
        draw.rectangle((0, HEIGHT - 220, WIDTH, HEIGHT), fill=fg)
        _draw_title(draw, title, title_font, fg, (70, 220, WIDTH - 70, 1080))
        draw.text((80, 1288), topic[:16], font=meta_font, fill=bg)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def generate_covers(title: str, topic: str) -> list[dict[str, str]]:
    import base64

    covers = []
    for name, bg, fg, accent in PALETTES:
        raw = render_cover(title, topic, name, fg, bg, accent)
        covers.append(
            {
                "id": name,
                "label": {"stamp": "朱红框", "paper": "样本纸", "ink": "炭黑", "index": "荧光签"}[name],
                "dataUrl": "data:image/png;base64," + base64.b64encode(raw).decode("ascii"),
            }
        )
    return covers
