"""
Enhanced PDF builder for expanded lecture notes (self-contained).

Layout:
  - Page 1: centered title splash
  - Pages 2..N: per-slide expanded notes (Overview, Core Ideas, Examples & Pitfalls)

No imports from pdf_builder.py to avoid cross-module signature/type mismatches.
"""

from __future__ import annotations

from io import BytesIO
import copy
from typing import Iterable, List, Tuple

from reportlab.lib.pagesizes import A4, A5, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# --------------------------------------------------------------------------------------
# Safety + color helpers
# --------------------------------------------------------------------------------------

def _assert_theme_dict(theme):
    if not isinstance(theme, dict):
        raise TypeError("[pdf_enhanced] theme must be dict.")

def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))

def _hex_to_rgb01(hex_str: str) -> Tuple[float, float, float]:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(ch*2 for ch in h)
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return r, g, b

def _luminance(hex_str: str) -> float:
    r, g, b = _hex_to_rgb01(hex_str)
    def srgb_to_lin(c):
        return c/12.92 if c <= 0.03928 else ((c+0.055)/1.055) ** 2.4
    R, G, B = srgb_to_lin(r), srgb_to_lin(g), srgb_to_lin(b)
    return 0.2126*R + 0.7152*G + 0.0722*B

def _contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    L1 = _luminance(fg_hex)
    L2 = _luminance(bg_hex)
    if L1 < L2:
        L1, L2 = L2, L1
    return (L1 + 0.05) / (L2 + 0.05)

def _accessible_text_color(bg_hex: str, light="#FFFFFF", dark="#111111", min_ratio=4.5) -> str:
    # prefer whichever passes; if both pass, pick higher contrast
    cr_light = _contrast_ratio(light, bg_hex)
    cr_dark  = _contrast_ratio(dark, bg_hex)
    if cr_light >= min_ratio and cr_dark >= min_ratio:
        return light if cr_light >= cr_dark else dark
    if cr_light >= min_ratio:
        return light
    if cr_dark >= min_ratio:
        return dark
    return light if cr_light >= cr_dark else dark

# --------------------------------------------------------------------------------------
# Page & theme helpers
# --------------------------------------------------------------------------------------

def _choose_page_size(plan) -> Tuple[float, float]:
    preset = (getattr(plan, "device_preset", None) or "").lower()
    orientation = (getattr(plan, "orientation", None) or "auto").lower()

    if preset == "desktop":
        return landscape(A4)
    if preset == "tablet":
        return A4
    if preset == "mobile":
        return A5

    if orientation == "landscape":
        return landscape(A4)
    # default -> landscape feels best on desktop
    return landscape(A4)

def _compute_scale(page_w_pts: float, base_w_pts: float = 595.0) -> float:
    try:
        scale = float(page_w_pts) / float(base_w_pts)
    except Exception:
        scale = 1.0
    return max(0.85, min(1.15, scale))

def _apply_scale_to_theme(theme: dict, scale: float) -> dict:
    _assert_theme_dict(theme)
    t = copy.deepcopy(theme)
    sizes = dict(t.get("sizes", {}))

    for key in ("display", "title", "h2", "h3", "body", "footer"):
        val = sizes.get(key)
        if isinstance(val, (int, float)):
            sizes[key] = int(round(val * scale))

    sizes["title"] = max(int(sizes.get("title", 20)), 18)
    sizes["body"] = max(int(sizes.get("body", 12)), 11)
    sizes["footer"] = max(int(sizes.get("footer", 10)), 9)

    t["sizes"] = sizes
    return t

def _safe_frame(page_w: float, page_h: float, theme: dict) -> Tuple[float, float, float, float]:
    margins = theme.get("margins", {}) or {}
    layout = theme.get("layout", {}) or {}
    left   = float(layout.get("safe_left",   margins.get("left",   48)))
    right  = float(layout.get("safe_right",  margins.get("right",  48)))
    top    = float(layout.get("safe_top",    margins.get("top",    64)))
    bottom = float(layout.get("safe_bottom", margins.get("bottom", 64)))
    w = max(0.0, page_w - left - right)
    h = max(0.0, page_h - top  - bottom)
    return left, bottom, w, h

# --------------------------------------------------------------------------------------
# Local drawing primitives
# --------------------------------------------------------------------------------------

def _string_width(c: canvas.Canvas, text: str, font: str, size: int) -> float:
    return c.stringWidth(text or "", font, size)

def _wrap_text(c: canvas.Canvas, text: str, font: str, size: int, max_width: float) -> List[str]:
    if not text:
        return []
    words = (text or "").split()
    lines: List[str] = []
    cur: List[str] = []
    for w in words:
        trial = (" ".join(cur + [w])).strip()
        if _string_width(c, trial, font, size) <= max_width or not cur:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

def _draw_paragraph_block(c, text, x, y, w, font, size, color_hex, leading_mult=1.35) -> float:
    c.setFont(font, size)
    c.setFillColor(HexColor(color_hex))
    lines = _wrap_text(c, text, font, size, w)
    leading = size * leading_mult
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y

def _draw_bullet_block(
    c,
    items,
    x,
    y,
    w,
    font,
    size,
    color_hex,
    marker="square",     # "square" | "dot"
    leading_mult=1.32,   # slightly tighter than paragraphs
    indent=18.0,         # text indent from marker edge
    marker_size=6.0,     # fixed marker size (pt)
    gap=6.0              # gap between marker and text
) -> float:
    """
    Draws a uniform bullet list with fixed-size markers and aligned text.
    """
    c.setFont(font, size)
    c.setFillColor(HexColor(color_hex))

    # marker block width = marker + gap
    marker_block_w = marker_size + gap
    usable_w = max(0.0, w - indent - marker_block_w)
    leading = size * leading_mult

    for raw in (items or []):
        text = (raw or "").strip()
        if not text:
            continue

        # marker baseline aligns with first text line baseline
        marker_x = x
        marker_y = y - (size * 0.75) + (marker_size * 0.5)

        if marker == "dot":
            # draw a filled circle
            c.circle(marker_x + marker_size / 2.0, marker_y, marker_size / 2.0, stroke=0, fill=1)
        else:
            # draw a filled square
            c.rect(marker_x, marker_y - marker_size / 2.0, marker_size, marker_size, stroke=0, fill=1)

        # wrap the bullet text
        text_x = x + indent + marker_block_w
        y = _draw_paragraph_block(c, text, text_x, y, usable_w, font, size, color_hex, leading_mult)

        # inter-item gap
        y -= max(4.0, size * 0.18)

    return y


def draw_page_background(c: canvas.Canvas, theme: dict, page_w: float, page_h: float):
    _assert_theme_dict(theme)
    colors = theme.get("colors", {})
    bg = colors.get("bg", "#FFFFFF")
    c.setFillColor(HexColor(bg))
    c.rect(0, 0, page_w, page_h, stroke=0, fill=1)

def draw_footer(c: canvas.Canvas, theme: dict, page_w: float, page_h: float, page_num: int):
    fonts = theme.get("fonts", {})
    sizes = theme.get("sizes", {})
    colors = theme.get("colors", {})
    text_hex = colors.get("muted", colors.get("text", "#333333"))
    c.setFont(fonts.get("body", "Helvetica"), int(sizes.get("footer", 10)))
    c.setFillColor(HexColor(text_hex))
    label = f"Page {page_num}"
    tw = _string_width(c, label, fonts.get("body", "Helvetica"), int(sizes.get("footer", 10)))
    c.drawString((page_w - tw) / 2.0, 18, label)

def draw_title_in_band(c, title, band_top, band_h, theme, page_w, align="left"):
    colors = theme.get("colors", {})
    fonts  = theme.get("fonts", {})
    sizes  = theme.get("sizes", {})
    band_hex = colors.get("accent", "#222222")
    text_hex = _accessible_text_color(band_hex)
    y0 = band_top - band_h
    c.setFillColor(HexColor(band_hex))
    c.rect(0, y0, page_w, band_h, stroke=0, fill=1)

    title_font = fonts.get("title", "Helvetica-Bold")
    title_size = int(sizes.get("h2", sizes.get("title", 20)))
    c.setFont(title_font, title_size)
    c.setFillColor(HexColor(text_hex))
    t = title or "Untitled"
    tw = _string_width(c, t, title_font, title_size)
    if align == "center":
        x = (page_w - tw) / 2.0
    else:
        x = 24.0
    c.drawString(x, y0 + (band_h - title_size) / 2.0, t)

def get_content_frame(page_w: float, page_h: float, theme: dict) -> Tuple[float, float, float, float]:
    return _safe_frame(page_w, page_h, theme)

# --------------------------------------------------------------------------------------
# Expanded content renderer
# --------------------------------------------------------------------------------------

def draw_expanded_content(c, slide, theme, content_x, content_y, content_w, content_h) -> float:
    fonts  = theme.get("fonts", {})
    sizes  = theme.get("sizes", {})
    colors = theme.get("colors", {})
    bg     = colors.get("bg", "#FFFFFF")
    body_font = fonts.get("body", "Helvetica")
    body_size = int(sizes.get("body", 12))
    hdr_font  = fonts.get("title", "Helvetica-Bold")
    hdr_size  = int(sizes.get("h2", sizes.get("title", 20)))
    hdr_hex   = colors.get("accent", "#2563EB")
    text_hex  = _accessible_text_color(bg)

    y = content_y

    # A) Overview (was Main Narrative)
    narrative = getattr(slide, "expanded_content", None)
    if narrative:
        c.setFont(hdr_font, hdr_size)
        c.setFillColor(HexColor(hdr_hex))
        c.drawString(content_x, y, "Overview")
        y -= hdr_size * 1.2

        if isinstance(narrative, str):
            y = _draw_paragraph_block(c, narrative, content_x, y, content_w, body_font, body_size, text_hex)
        else:
            for para in narrative:
                y = _draw_paragraph_block(c, para, content_x, y, content_w, body_font, body_size, text_hex)
                y -= max(6.0, body_size * 0.2)

        y -= max(8.0, body_size * 0.3)

    # B) Core Ideas (was Key Concepts)
    concepts = getattr(slide, "key_concepts", None)
    if concepts:
        c.setFont(hdr_font, hdr_size)
        c.setFillColor(HexColor(hdr_hex))
        c.drawString(content_x, y, "Core Ideas")
        y -= hdr_size * 1.2

        y = _draw_bullet_block(
            c, concepts, content_x, y, content_w, body_font, body_size, text_hex,
            marker="square", indent=18.0, marker_size=6.0
        )
        y -= max(8.0, body_size * 0.3)

    # C) Examples & Pitfalls (was Supporting Details)
    details = getattr(slide, "supporting_details", None)
    if details:
        c.setFont(hdr_font, hdr_size)
        c.setFillColor(HexColor(hdr_hex))
        c.drawString(content_x, y, "Examples & Pitfalls")
        y -= hdr_size * 1.2

        y = _draw_bullet_block(
            c, details, content_x, y, content_w, body_font, body_size, text_hex,
            marker="dot", indent=18.0, marker_size=6.0
        )

        y -= max(8.0, body_size * 0.3)

    return y

# --------------------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------------------

def _draw_center_title_fitted(c, title, theme, page_w, page_h):
    fonts = theme["fonts"]; sizes = theme["sizes"]; colors = theme["colors"]
    bg = colors.get("bg", "#FFFFFF")
    cf_x, cf_y, cf_w, cf_h = get_content_frame(page_w, page_h, theme)

    font = fonts.get("display", fonts.get("title", "Helvetica-Bold"))
    size = int(sizes.get("display", sizes.get("title", 28)))
    min_size = max(18, int(sizes.get("title", 20)))
    max_width = cf_w * 0.9

    c.setFillColor(HexColor(_accessible_text_color(bg)))
    text = title or "Untitled"

    while size > min_size and c.stringWidth(text, font, size) > max_width:
        size -= 1

    lines = [text]
    if c.stringWidth(text, font, size) > max_width:
        words = text.split()
        lines = []
        cur = []
        for w in words:
            trial = (" ".join(cur + [w])).strip()
            if c.stringWidth(trial, font, size) <= max_width or not cur:
                cur.append(w)
            else:
                lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))
        if len(lines) > 2:
            head = lines[0]
            tail = " ".join(lines[1:])
            ell = "…"
            while size > min_size and c.stringWidth(tail + ell, font, size) > max_width:
                size -= 1
            lines = [head, tail + ell]

    leading = size * 1.1
    total_h = size if len(lines) == 1 else size + leading
    start_y = cf_y + cf_h/2 + total_h/2 - size

    c.setFont(font, size)
    for i, line in enumerate(lines[:2]):
        tw = c.stringWidth(line, font, size)
        x = cf_x + (cf_w - tw) / 2.0
        y = start_y - i * leading
        c.drawString(x, y, line)

def build_enhanced_pdf(plan, theme: dict, **kwargs) -> bytes:
    _assert_theme_dict(theme)

    page_w, page_h = _choose_page_size(plan)
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))
    c.setTitle(getattr(plan, "topic", "EduSynth Notes"))

    scale = _compute_scale(page_w)
    theme_eff = _apply_scale_to_theme(theme, scale)
    fonts  = theme_eff.get("fonts", {})
    sizes  = theme_eff.get("sizes", {})
    colors = theme_eff.get("colors", {})
    spacing = theme_eff.get("spacing", {"sm":8,"md":12,"lg":16,"xl":24})
    band_cfg = theme_eff.get("band", {"height_em":2.0, "gap_below_em":0.9})

    # Page 1: Title splash
    draw_page_background(c, theme_eff, page_w, page_h)
    _draw_center_title_fitted(c, getattr(plan, "topic", "Untitled"), theme_eff, page_w, page_h)
    draw_footer(c, theme_eff, page_w, page_h, page_num=1)
    c.showPage()

    # Slides
    page_num = 2
    slides = list(getattr(plan, "slides", []))
    cf_x, cf_y, cf_w, cf_h = get_content_frame(page_w, page_h, theme_eff)
    safe_top = float(theme_eff.get("layout", {}).get("safe_top", 48.0))

    for slide in slides:
        draw_page_background(c, theme_eff, page_w, page_h)

        # Header band (contrast-safe)
        h2_size = int(sizes.get("h2", sizes.get("title", 20)))
        band_h = max(48, int(h2_size * float(band_cfg.get("height_em", 2.0))))
        band_top = page_h - safe_top / 2.0
        draw_title_in_band(c, getattr(slide, "title", "Untitled"), band_top, band_h, theme_eff, page_w, align="left")

        # Content start: always below band with clear gap
        band_gap = int(h2_size * float(band_cfg.get("gap_below_em", 0.9)))
        start_y = min(
            cf_y + cf_h - int(h2_size * 0.6),
            band_top - (band_h + band_gap)
        )


        _ = draw_expanded_content(
            c=c,
            slide=slide,
            theme=theme_eff,
            content_x=cf_x,
            content_y=start_y,
            content_w=cf_w,
            content_h=cf_h,
        )

        draw_footer(c, theme_eff, page_w, page_h, page_num=page_num)
        c.showPage()
        page_num += 1

    c.save()
    return buf.getvalue()
