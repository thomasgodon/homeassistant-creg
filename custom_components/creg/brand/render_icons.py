#!/usr/bin/env python3
"""Render icon.png (256x256) and icon@2x.png (512x512) for the CREG Tariff integration."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BRAND_DIR = Path(__file__).parent

GREEN = (76, 175, 80, 255)
DARK  = (26, 26, 26, 255)
WHITE = (255, 255, 255, 255)

# FontAwesome-bolt-style polygon, normalized to bounding box (0..1)
BOLT_NORM = [
    (0.750, 0.000),
    (0.000, 0.438),
    (0.417, 0.438),
    (0.250, 1.000),
    (1.000, 0.563),
    (0.583, 0.563),
]

BOLD_FONTS = [
    r"C:\Windows\Fonts\seguibl.ttf",   # Segoe UI Black
    r"C:\Windows\Fonts\arialbd.ttf",   # Arial Bold
    r"C:\Windows\Fonts\calibrib.ttf",  # Calibri Bold
    r"C:\Windows\Fonts\verdanab.ttf",  # Verdana Bold
]

CAPTION_FONTS = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
    r"C:\Windows\Fonts\verdanab.ttf",
]


def load_font(paths: list[str], size: int) -> ImageFont.FreeTypeFont:
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def scale_poly(norm_pts, x: float, y: float, w: float, h: float) -> list[tuple[float, float]]:
    return [(x + px * w, y + py * h) for px, py in norm_pts]


def draw_icon(size: int) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded-square background
    radius = int(size * 0.14)
    draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=DARK)

    # Main wordmark font
    font_size = int(size * 0.295)
    font      = load_font(BOLD_FONTS, font_size)

    # Measure letter groups — textbbox origin is (0,0); box is (left, top, right, bottom)
    cr_box = draw.textbbox((0, 0), "CR", font=font)
    g_box  = draw.textbbox((0, 0), "G",  font=font)
    cr_w = cr_box[2] - cr_box[0]
    cr_h = cr_box[3] - cr_box[1]
    g_w  = g_box[2]  - g_box[0]
    cap_h = cr_h

    bolt_w = int(cap_h * 0.50)
    gap    = int(size * 0.015)

    # Subtitle font + measurements
    sub_font_size = int(size * 0.088)
    sub_font = load_font(CAPTION_FONTS, sub_font_size)
    sub_box  = draw.textbbox((0, 0), "TARIFF", font=sub_font)
    sub_h    = sub_box[3] - sub_box[1]

    line_h   = max(1, int(size * 0.007))
    line_gap = int(size * 0.040)
    sub_gap  = int(size * 0.030)

    total_mark_w = cr_w + gap + bolt_w + gap + g_w
    total_h      = cap_h + line_gap + line_h + sub_gap + sub_h

    # Center the whole mark vertically and horizontally
    mark_x = (size - total_mark_w) // 2
    mark_y = (size - total_h) // 2

    # "CR"
    draw.text((mark_x - cr_box[0], mark_y - cr_box[1]), "CR", font=font, fill=GREEN)

    # Lightning bolt
    bx = mark_x + cr_w + gap
    by = mark_y
    draw.polygon(scale_poly(BOLT_NORM, bx, by, bolt_w, cap_h), fill=GREEN)

    # "G"
    gx = bx + bolt_w + gap
    draw.text((gx - g_box[0], mark_y - g_box[1]), "G", font=font, fill=GREEN)

    # Underline
    line_y = mark_y + cap_h + line_gap
    draw.rectangle(
        [(mark_x, line_y), (mark_x + total_mark_w - 1, line_y + line_h - 1)],
        fill=GREEN,
    )

    # "TARIFF" subtitle
    sub_x = (size - (sub_box[2] - sub_box[0])) // 2
    sub_y = line_y + line_h + sub_gap
    draw.text((sub_x - sub_box[0], sub_y - sub_box[1]), "TARIFF", font=sub_font, fill=WHITE)

    return img


if __name__ == "__main__":
    for size, name in [(256, "icon.png"), (512, "icon@2x.png")]:
        out = BRAND_DIR / name
        draw_icon(size).save(out, "PNG")
        print(f"Saved {out}  ({size}x{size})")
