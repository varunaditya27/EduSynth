from __future__ import annotations

import math
import random
import copy
from io import BytesIO
from typing import List, Tuple

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A5, landscape, portrait
from reportlab.lib.colors import HexColor, white

from app.schemas.slides import LecturePlan, SlideItem
from .icons import get_semantic_icon, POINT_SPACING_PT
from .diagram_draw import (
    polar_to_xy,
    layout_radial,
    draw_bezier_connector,
    lighten,
    darken,
    vignette_overlay,
    text_wrap,
    node_size_for_text,
    rounded_rect,
    curved_arrow,
    progress_bar,
    content_frame as compute_frame,
    clamp_title,
    measure_lines_height,
)

# -------------------------------------------------------------------
# PUBLIC
# -------------------------------------------------------------------

def build_pdf(
    plan: LecturePlan,
    theme: dict,
    cheatsheet_only: bool = False,
    notes_only: bool = False,
    no_ornaments: bool = False,
    no_dropcaps: bool = False,
) -> bytes:
    """Builds: Title Splash (pg1), Flowchart (pg2), Notes (rest) with adaptive layout."""
    buf = BytesIO()
    
    # Determine page size based on device_preset or orientation
    page_w, page_h = _determine_page_size(plan)
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))
    
    # Compute content frame and adaptive scaling
    cf_x, cf_y, cf_w, cf_h = compute_frame(page_w, page_h, theme)
    scale = _compute_scale(cf_w)
    
    # Create scaled theme (local copy, don't mutate original)
    theme_local = _apply_scale_to_theme(theme, scale)
    
    # Simple page count like the original working version
    total_pages = (2 if not notes_only else 0) + (0 if cheatsheet_only else len(plan.slides))

    if not notes_only:
        draw_title_splash(c, plan, theme_local, page_w, page_h)
        draw_footer(c, plan, page_index=1, total_pages=total_pages, theme=theme_local, page_w=page_w, page_h=page_h)
        c.showPage()

        draw_flowchart(c, plan, theme_local, page_w, page_h)
        draw_footer(c, plan, page_index=2, total_pages=total_pages, theme=theme_local, page_w=page_w, page_h=page_h)
        c.showPage()

    if not cheatsheet_only:
        for i, slide in enumerate(plan.slides, start=1):
            draw_notes_page(c, slide, i, len(plan.slides), plan, theme_local, page_w, page_h)
            draw_footer(
                c,
                plan,
                page_index=(2 + i) if not notes_only else i,
                total_pages=total_pages,
                theme=theme_local,
                page_w=page_w,
                page_h=page_h,
            )
            c.showPage()

    c.save()
    buf.seek(0)
    return buf.read()

# -------------------------------------------------------------------
# ADAPTIVE SIZING HELPERS
# -------------------------------------------------------------------

def _determine_page_size(plan: LecturePlan) -> Tuple[float, float]:
    """Determine page size based on device_preset or orientation."""
    # Device preset takes priority
    if plan.device_preset == "desktop":
        return landscape(A4)
    elif plan.device_preset == "tablet":
        return portrait(A4)
    elif plan.device_preset == "mobile":
        return portrait(A5)
    
    # Fall back to orientation
    orientation_mode = plan.orientation or "auto"
    
    if orientation_mode == "portrait":
        return portrait(A4)
    elif orientation_mode == "landscape":
        return landscape(A4)
    else:  # "auto"
        # Try landscape first, check if content frame is wide enough
        page_w, page_h = landscape(A4)
        if page_w > 720:
            return landscape(A4)
        else:
            return portrait(A4)

def _compute_scale(cf_w: float) -> float:
    """Compute typography scale based on content frame width."""
    base_w = 720.0
    scale = max(0.85, min(1.15, cf_w / base_w))
    return scale

def _apply_scale_to_theme(theme: dict, scale: float) -> dict:
    """Create a scaled copy of theme with adjusted sizes."""
    theme_local = copy.deepcopy(theme)
    sizes = theme_local["sizes"]
    
    # Scale typography
    sizes["display"] = max(18, int(sizes["display"] * scale))
    sizes["title"] = max(18, int(sizes["title"] * scale))
    sizes["h2"] = max(18, int(sizes["h2"] * scale))
    sizes["h3"] = max(14, int(sizes["h3"] * scale))
    sizes["body"] = max(11, int(sizes["body"] * scale))
    sizes["footer"] = max(9, int(sizes["footer"] * scale))
    
    return theme_local

# -------------------------------------------------------------------
# BACKGROUND + SAFE AREA
# -------------------------------------------------------------------

def draw_page_background(c: canvas.Canvas, page_w: float, page_h: float, theme: dict) -> None:
    bg_hex = theme["colors"]["bg"]
    c.setFillColor(HexColor(bg_hex))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    vignette_overlay(c, page_w, page_h, strength=theme.get("vignette", {}).get("strength", 0.06))

def get_content_frame(page_w: float, page_h: float, theme: dict) -> tuple[float,float,float,float]:
    return compute_frame(page_w, page_h, theme)

# -------------------------------------------------------------------
# HEADER/FOOTER + TITLES
# -------------------------------------------------------------------

def draw_title_in_band(
    c: canvas.Canvas,
    text: str,
    band_top: float,
    band_height: float,
    theme: dict,
    page_w: float,
    align: str = "left",
) -> float:
    """Render title inside a horizontal band; returns baseline y used for subsequent content."""
    fonts = theme["fonts"]; sizes = theme["sizes"]; layout = theme["layout"]; colors = theme["colors"]
    left = max(theme["layout"]["safe_left"], theme["margins"]["left"])
    right = page_w - max(theme["layout"]["safe_right"], theme["margins"]["right"])
    max_width = right - left

    size, lines = clamp_title(c, text, fonts["title"], sizes["title"], layout["title_min_size"], max_width)
    leading = size * 1.1
    total_h = measure_lines_height(size, len(lines), 1.1)

    # vertical placement (center within band)
    y_center = band_top - band_height/2
    start_y = y_center + (total_h/2) - size

    c.setFillColor(HexColor(colors["text"]))
    c.setFont(fonts["title"], size)

    for i, line in enumerate(lines):
        tw = c.stringWidth(line, fonts["title"], size)
        if align == "center":
            x = (left + right)/2 - tw/2
        else:
            x = left
        y = start_y - i * leading
        c.drawString(x, y, line)

    return band_top - band_height

def draw_footer(
    c: canvas.Canvas,
    plan: LecturePlan,
    page_index: int,
    total_pages: int,
    theme: dict,
    page_w: float,
    page_h: float,
):
    colors = theme["colors"]; sizes = theme["sizes"]; layout = theme["layout"]
    left = max(layout["safe_left"], theme["margins"]["left"])
    right = page_w - max(layout["safe_right"], theme["margins"]["right"])
    bottom = layout["safe_bottom"]

    # divider
    c.setStrokeColor(HexColor(colors["muted"]))
    c.setLineWidth(0.8)
    c.line(left, bottom + 10, right, bottom + 10)

    # folio text
    c.setFont(theme["fonts"]["body"], sizes["footer"])
    c.setFillColor(HexColor(colors["muted"]))
    folio = f"{plan.topic} • {page_index}/{total_pages} • {plan.theme}"
    tw = c.stringWidth(folio, theme["fonts"]["body"], sizes["footer"])
    
    theme_key = plan.theme.lower()
    if theme_key == "minimalist":
        x = (page_w - tw)/2
    elif theme_key == "chalkboard":
        x = max(layout["safe_left"], theme["margins"]["left"])
    else:
        x = right - tw
    c.drawString(x, bottom, folio)

# -------------------------------------------------------------------
# PAGE 1: TITLE SPLASH
# -------------------------------------------------------------------

def draw_title_splash(c: canvas.Canvas, plan: LecturePlan, theme: dict, page_w: float, page_h: float):
    """Title-only splash: perfectly centered inside safe content frame."""
    draw_page_background(c, page_w, page_h, theme)

    fonts = theme["fonts"]; sizes = theme["sizes"]; layout = theme["layout"]; colors = theme["colors"]

    cf_x, cf_y, cf_w, cf_h = get_content_frame(page_w, page_h, theme)

    max_width = cf_w * 0.90
    start_size = sizes["display"]
    min_size = layout["title_min_size"]
    size, lines = clamp_title(c, plan.topic, fonts["title"], start_size, min_size, max_width)

    leading = size * 1.10
    total_h = measure_lines_height(size, len(lines), 1.10)

    center_y = cf_y + cf_h / 2.0
    start_y = center_y + (total_h / 2.0) - size

    c.setFont(fonts["title"], size)
    c.setFillColor(HexColor(colors["text"]))

    for i, line in enumerate(lines):
        tw = c.stringWidth(line, fonts["title"], size)
        x = cf_x + (cf_w - tw) / 2.0
        y = start_y - i * leading
        c.drawString(x, y, line)

# -------------------------------------------------------------------
# PAGE 2: FLOWCHART (RESPONSIVE GRID)
# -------------------------------------------------------------------

def draw_flowchart(c: canvas.Canvas, plan: LecturePlan, theme: dict, page_w: float, page_h: float):
    draw_page_background(c, page_w, page_h, theme)
    colors = theme["colors"]; sizes = theme["sizes"]; layout = theme["layout"]
    cf_x, cf_y, cf_w, cf_h = get_content_frame(page_w, page_h, theme)

    # header band
    band_h = 56
    band_top = page_h - layout["safe_top"]/2
    draw_title_in_band(c, "Process Flow", band_top, band_h, theme, page_w, align="left")

    # pick slide
    proc = None
    for s in plan.slides:
        if getattr(s, "diagram", None) == "process":
            proc = s; break
    if not proc and plan.slides:
        proc = plan.slides[0]
    if not proc: return

    steps = proc.points[:6]
    if not steps: return

    # Responsive grid layout
    theme_key = plan.theme.lower()
    gap_x = 28
    gap_y = 34
    target_box_w = max(160, min(220, cf_w/3 - gap_x))
    cols = max(1, min(3, int((cf_w + gap_x) / (target_box_w + gap_x))))
    rows = math.ceil(len(steps) / cols)
    median_w = target_box_w
    box_h = 104 if theme_key == "chalkboard" else 96

    # Calculate total grid size
    total_grid_w = cols * median_w + (cols - 1) * gap_x
    total_grid_h = rows * box_h + (rows - 1) * gap_y
    
    # Center grid in content frame
    start_x = cf_x + (cf_w - total_grid_w) / 2
    start_y = cf_y + (cf_h - total_grid_h) / 2 + total_grid_h - box_h

    for i, text in enumerate(steps):
        row = i // cols
        col = i % cols
        
        bx = start_x + col * (median_w + gap_x)
        by = start_y - row * (box_h + gap_y)

        # Ensure box inside frame
        bx = max(bx, cf_x)
        if bx + median_w > cf_x + cf_w:
            bx = cf_x + cf_w - median_w

        # body
        c.setFillColor(white if theme_key != "chalkboard" else HexColor(lighten(colors["accent"], 0.35 if i%2==0 else 0.2)))
        rounded_rect(c, bx, by, median_w, box_h, 24 if theme_key=="minimalist" else 8 if theme_key=="chalkboard" else 6, fill=True, stroke=False)
        
        # stripe/stroke
        accent = colors["accent"] if i % 2 == 0 else colors["accent2"]
        if theme_key == "corporate":
            c.setFillColor(HexColor(accent))
            c.rect(bx, by + box_h - 10, median_w, 10, fill=1, stroke=0)
        c.setStrokeColor(HexColor(accent))
        c.setLineWidth(2.0 if theme_key != "chalkboard" else 3.0)
        rounded_rect(c, bx, by, median_w, box_h, 24 if theme_key=="minimalist" else 8 if theme_key=="chalkboard" else 6, fill=False, stroke=True)

        # label text
        label = text if len(text) <= 40 else text[:40] + "..."
        c.setFont(theme["fonts"]["body"], 13)
        c.setFillColor(HexColor(colors["text"] if theme_key != "chalkboard" else colors["bg"]))
        lines = text_wrap(c, label, theme["fonts"]["body"], 13, median_w - 28)
        ty = by + box_h/2 + 6
        for ln in lines[:3]:
            c.drawString(bx + 14, ty, ln)
            ty -= 16

        # arrows
        y_center = by + box_h/2
        
        # Right arrow (if not last in row and not last item)
        if col < cols - 1 and i < len(steps) - 1:
            x0 = bx + median_w
            x1 = x0 + gap_x
            curved_arrow(c, x0, y_center, x1, y_center, 
                        color_hex=colors["accent2"] if i%2==0 else colors["accent"], 
                        width=1.6 if theme_key != "chalkboard" else 2.2, head=9)
        
        # Down arrow (if last in row and not last item overall)
        elif col == cols - 1 and i < len(steps) - 1:
            next_row = (i + 1) // cols
            next_col = (i + 1) % cols
            next_bx = start_x + next_col * (median_w + gap_x)
            next_by = start_y - next_row * (box_h + gap_y)
            
            # Draw downward connector
            x_start = bx + median_w / 2
            y_start = by
            x_end = next_bx + median_w / 2
            y_end = next_by + box_h
            
            curved_arrow(c, x_start, y_start, x_end, y_end,
                        color_hex=colors["accent2"] if i%2==0 else colors["accent"],
                        width=1.6 if theme_key != "chalkboard" else 2.2, head=9)

    # progress bar
    bar_w = min(cf_w*0.8, 560)
    progress_bar(c, cf_x + (cf_w-bar_w)/2, cf_y + 18, bar_w, 8, 
                steps=len(steps), current=len(steps), 
                accent_hex=colors["accent"], muted_hex=colors["muted"])

# -------------------------------------------------------------------
# NOTES PAGES (uniform bullets, no overlap)
# -------------------------------------------------------------------

def draw_notes_page(
    c: canvas.Canvas,
    slide: SlideItem,
    idx: int,
    total: int,
    plan: LecturePlan,
    theme: dict,
    page_w: float,
    page_h: float,
):
    draw_page_background(c, page_w, page_h, theme)
    colors = theme["colors"]; sizes = theme["sizes"]; layout = theme["layout"]

    cf_x, cf_y, cf_w, cf_h = get_content_frame(page_w, page_h, theme)

    # header band
    band_h = 72 if plan.theme=="chalkboard" else 64
    band_top = page_h - layout["safe_top"]/2
    title_bottom = draw_title_in_band(c, slide.title, band_top, band_h, theme, page_w, align="left")

    # compute content region (under band, above footer)
    top_y = min(title_bottom - 10, cf_y + cf_h - 20)
    x = cf_x
    max_w = cf_w

    _draw_bulleted_paragraphs(c, x, top_y, max_w, slide.points, theme)

def _draw_bulleted_paragraphs(c: canvas.Canvas, x: float, y_top: float, max_w: float, points: List[str], theme: dict):
    colors = theme["colors"]; sizes = theme["sizes"]; layout = theme["layout"]
    body_fs = sizes["body"]
    leading = body_fs * layout["bullet_leading"]
    para_gap = layout["para_gap_pt"]
    indent = layout["bullet_indent_pt"]

    y = y_top
    for i, p in enumerate(points):
        # stop before footer band
        min_y = layout["safe_bottom"] + 36
        if y < min_y:
            break  # simple stop to avoid overlap

        # icon / marker
        c.setFillColor(HexColor(colors["accent2"]))
        if theme is not None and "corporate" in str(theme.get("colors", "")):
            c.rect(x, y - 3, 6, 6, fill=1, stroke=0)
        else:
            c.circle(x + 3, y, 3, fill=1, stroke=0)

        # text
        c.setFont(theme["fonts"]["body"], body_fs)
        c.setFillColor(HexColor(colors["text"]))
        expanded = _expand_point(p)
        lines = text_wrap(c, expanded, theme["fonts"]["body"], body_fs, max_w - indent - 6)
        for ln in lines[:4]:
            c.drawString(x + indent, y, ln)
            y -= leading
        y -= para_gap

# -------------------------------------------------------------------
# UTIL
# -------------------------------------------------------------------

def _expand_point(point: str) -> str:
    variants = [
        f"{point}. This forms a core building block and should be understood before moving to advanced patterns.",
        f"{point}. Keep practical constraints in mind and be explicit about assumptions while reasoning.",
        f"{point}. Use small traced examples to validate the logic and avoid hidden edge cases.",
        f"{point}. Consider performance trade-offs and memory overhead as inputs scale.",
    ]
    return random.choice(variants)