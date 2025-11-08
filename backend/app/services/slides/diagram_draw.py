from __future__ import annotations

import math
from typing import List, Tuple

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

# ---- color utils ----

def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def _hex_to_rgb_tuple(hex_color: str) -> Tuple[int, int, int]:
    hc = hex_color.lstrip("#")
    return tuple(int(hc[i:i+2], 16) for i in (0, 2, 4))

def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    r, g, b = _hex_to_rgb_tuple(hex_color)
    return (r/255.0, g/255.0, b/255.0)

def lighten(hex_color: str, amount: float) -> str:
    r, g, b = _hex_to_rgb_tuple(hex_color)
    r = int(_clamp01(r/255.0 + amount) * 255)
    g = int(_clamp01(g/255.0 + amount) * 255)
    b = int(_clamp01(b/255.0 + amount) * 255)
    return f"#{r:02X}{g:02X}{b:02X}"

def darken(hex_color: str, amount: float) -> str:
    r, g, b = _hex_to_rgb_tuple(hex_color)
    r = int(_clamp01(r/255.0 - amount) * 255)
    g = int(_clamp01(g/255.0 - amount) * 255)
    b = int(_clamp01(b/255.0 - amount) * 255)
    return f"#{r:02X}{g:02X}{b:02X}"

# ---- geometry helpers ----

def polar_to_xy(cx: float, cy: float, r: float, theta_rad: float) -> Tuple[float, float]:
    return (cx + r * math.cos(theta_rad), cy + r * math.sin(theta_rad))

def layout_radial(nodes: List[dict], radius: float, relax_iters: int = 4) -> List[Tuple[float, float, float]]:
    """Return list of (x_rel, y_rel, theta) after light collision-aware relaxation."""
    n = max(1, len(nodes))
    base = [2*math.pi * i / n - math.pi/2 for i in range(n)]
    coords = []
    for i, theta in enumerate(base):
        w = nodes[i]["width"]; h = nodes[i]["height"]
        x, y = radius*math.cos(theta), radius*math.sin(theta)
        coords.append([x, y, theta, w, h])

    # very light repel to prevent overlaps
    for _ in range(relax_iters):
        for i in range(n):
            xi, yi, thetai, wi, hi = coords[i]
            ri = max(wi, hi) * 0.6
            for j in range(i+1, n):
                xj, yj, thetaj, wj, hj = coords[j]
                rj = max(wj, hj) * 0.6
                dx, dy = xj - xi, yj - yi
                dist = math.hypot(dx, dy) or 1.0
                min_d = ri + rj + 12  # gutter
                if dist < min_d:
                    push = (min_d - dist) / 2.0
                    nx, ny = dx/dist, dy/dist
                    coords[i][0] -= nx * push
                    coords[i][1] -= ny * push
                    coords[j][0] += nx * push
                    coords[j][1] += ny * push

    return [(x, y, theta) for x, y, theta, _, _ in coords]

# ---- drawing helpers ----

def rounded_rect(c: canvas.Canvas, x: float, y: float, w: float, h: float, r: float, fill: bool=False, stroke: bool=False):
    c.roundRect(x, y, w, h, r, stroke=1 if stroke else 0, fill=1 if fill else 0)

def draw_bezier_connector(c: canvas.Canvas, x0: float, y0: float, x1: float, y1: float, t_bias: float = 0.5):
    # control points pulled towards the middle for a nice bow
    mx = (x0 + x1) / 2.0
    my = (y0 + y1) / 2.0
    cx1 = (x0 * (1 - t_bias)) + (mx * t_bias)
    cy1 = (y0 * (1 - t_bias)) + (my * t_bias)
    cx2 = (x1 * (1 - t_bias)) + (mx * t_bias)
    cy2 = (y1 * (1 - t_bias)) + (my * t_bias)

    p = c.beginPath()
    p.moveTo(x0, y0)
    p.curveTo(cx1, cy1, cx2, cy2, x1, y1)
    c.drawPath(p)

def vignette_overlay(c: canvas.Canvas, page_w: float, page_h: float, strength: float = 0.08):
    # simple vignette using expanding translucent rects
    steps = 16
    for i in range(steps):
        alpha = strength * (i+1)/steps
        c.setFillColorRGB(0,0,0, alpha=alpha)
        inset = 6 * (steps - i)
        c.rect(0 + inset, 0 + inset, page_w - 2*inset, page_h - 2*inset, fill=1, stroke=0)

def node_size_for_text(c: canvas.Canvas, text: str, font_name: str, font_size: float, padding=(16,12)) -> tuple[float,float]:
    c.setFont(font_name, font_size)
    w = c.stringWidth(text, font_name, font_size)
    h = font_size * 1.4
    return (w + padding[0]*2, h + padding[1]*2)

def text_wrap(c: canvas.Canvas, text: str, font_name: str, font_size: float, max_width: float) -> list[str]:
    c.setFont(font_name, font_size)
    words = text.split()
    lines = []
    cur = []
    for w in words:
        test = (" ".join(cur+[w])).strip()
        if c.stringWidth(test, font_name, font_size) <= max_width or not cur:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

def curved_arrow(c: canvas.Canvas, x0: float, y0: float, x1: float, y1: float, color_hex: str, width: float = 1.2, head: float = 8):
    c.setStrokeColor(HexColor(color_hex))
    c.setLineWidth(width)
    draw_bezier_connector(c, x0, y0, x1, y1, t_bias=0.5)
    # tiny arrow head
    angle = math.atan2(y1-y0, x1-x0)
    ax = x1 - head*math.cos(angle - 0.4)
    ay = y1 - head*math.sin(angle - 0.4)
    bx = x1 - head*math.cos(angle + 0.4)
    by = y1 - head*math.sin(angle + 0.4)
    p = c.beginPath()
    p.moveTo(x1, y1)
    p.lineTo(ax, ay)
    p.lineTo(bx, by)
    p.close()
    c.setFillColor(HexColor(color_hex))
    c.drawPath(p, fill=1, stroke=0)

def progress_bar(c: canvas.Canvas, x: float, y: float, w: float, h: float, steps: int, current: int, accent_hex: str, muted_hex: str):
    seg_w = w / steps
    for i in range(steps):
        color = accent_hex if i < current else muted_hex
        c.setFillColor(HexColor(color))
        c.rect(x + i*seg_w + 1, y, seg_w - 2, h, fill=1, stroke=0)

# ---- layout helpers (NEW) ----

def content_frame(page_w: float, page_h: float, theme: dict) -> tuple[float,float,float,float]:
    L = theme["layout"]; M = theme["margins"]
    x = max(L["safe_left"], M["left"])
    y = max(L["safe_bottom"], M["bottom"])
    w = page_w - x - max(L["safe_right"], M["right"])
    h = page_h - max(L["safe_top"], M["top"]) - y
    return (x, y, w, h)

def clamp_title(c: canvas.Canvas, text: str, font_name: str, start_size: float, min_size: float, max_width: float) -> tuple[float, list[str]]:
    """Return (size, lines<=2) that fit in max_width by shrinking or wrapping."""
    size = start_size
    # try keep one line by shrinking
    if c.stringWidth(text, font_name, size) <= max_width:
        return size, [text]
    # try shrink to min
    while size > min_size and c.stringWidth(text, font_name, size) > max_width:
        size -= 1
    if c.stringWidth(text, font_name, size) <= max_width:
        return size, [text]
    # wrap to 2 lines
    lines = text_wrap(c, text, font_name, size, max_width)
    if len(lines) > 2:
        lines = [" ".join(lines[:-1]), lines[-1]]
    return size, lines

def measure_lines_height(font_size: float, line_count: int, leading_multiplier: float) -> float:
    return font_size * leading_multiplier * line_count
