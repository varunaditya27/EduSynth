"""
PPTX builder with visual themes and adaptive layout matching PDF quality.
Simplified to heading + bullet points format only.
"""
from io import BytesIO
from typing import Dict, Any, Tuple, List, Optional
import math

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from PIL import Image, ImageDraw

from app.schemas.slides import LecturePlan, SlideItem
from .icons import get_point_icon
from .theme_tokens import get_theme


# --- Color Conversion Helpers ----------------------------------------------

def _hex_to_rgb_int(hex_color: str) -> Tuple[int, int, int]:
    """Convert #RRGGBB -> (r,g,b) ints 0..255."""
    hc = (hex_color or "#000000").lstrip("#")
    if len(hc) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    return tuple(int(hc[i : i + 2], 16) for i in (0, 2, 4))


def _blend_with_white(rgb: Tuple[int, int, int], alpha: float) -> Tuple[int, int, int]:
    """Blend RGB with white using alpha (0=white, 1=color)."""
    return tuple(int(255 * (1 - alpha) + c * alpha) for c in rgb)


def _srgb_to_linear(c: float) -> float:
    c = c / 255.0
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(rgb: Tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * _srgb_to_linear(r) + 0.7152 * _srgb_to_linear(g) + 0.0722 * _srgb_to_linear(b)


def _contrast_ratio(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    l1 = _relative_luminance(rgb1)
    l2 = _relative_luminance(rgb2)
    hi = max(l1, l2)
    lo = min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


# --- Math Helpers ----------------------------------------------------------

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _px_to_inches(px: float, dpi: float = 96.0) -> float:
    return float(px) / float(dpi)


# --- Slide Size / Presets --------------------------------------------------

PRESETS = {
    "desktop": (13.33, 7.5),   # 16:9 wide
    "tablet": (10.0, 7.5),     # 4:3 classic
    "mobile": (7.5, 13.33),    # 9:16 portrait
}


def _configure_slide_size(prs: Presentation, plan: LecturePlan) -> None:
    """Configure slide dimensions based on device_preset or orientation."""
    preset = (plan.device_preset or "").lower() if plan.device_preset else None
    orientation = (plan.orientation or "auto").lower()

    if preset and preset in PRESETS:
        w_in, h_in = PRESETS[preset]
    else:
        # Orientation-based fallback
        if orientation == "portrait":
            w_in, h_in = 7.5, 10.0  # 4:3 rotated
        elif orientation == "landscape":
            w_in, h_in = 10.0, 7.5  # 4:3 landscape
        else:  # auto
            w_in, h_in = PRESETS["desktop"]

    prs.slide_width = Inches(w_in)
    prs.slide_height = Inches(h_in)


# --- Adaptive Sizing -------------------------------------------------------

def _compute_scale_and_sizes(prs: Presentation, theme: Dict[str, Any]) -> Dict[str, float]:
    """Compute adaptive font sizes based on slide width."""
    base_w_in = 10.24
    margins = theme.get("margins", {})
    left_px = margins.get("left", 56)
    right_px = margins.get("right", 56)
    
    frame_w_in = prs.slide_width.inches - (_px_to_inches(left_px) + _px_to_inches(right_px))
    base_w_pts = base_w_in * 72.0
    frame_w_pts = frame_w_in * 72.0
    
    scale = _clamp(frame_w_pts / base_w_pts, 0.85, 1.15)

    sizes = theme.get("sizes", {})
    scaled = {
        "display": max(18, int(round(sizes.get("display", 46) * scale))),
        "title": max(18, int(round(sizes.get("title", 38) * scale))),
        "h2": max(18, int(round(sizes.get("h2", 28) * scale))),
        "body": max(12, int(round(sizes.get("body", 14) * scale))),
        "footer": max(10, int(round(sizes.get("footer", 10) * scale))),
    }
    return scaled


def _get_safe_frame(prs: Presentation, theme: Dict[str, Any]) -> Tuple[float, float, float, float]:
    """Return (left, top, width, height) in inches for content frame."""
    layout = theme.get("layout", {})
    margins = theme.get("margins", {})
    
    left = max(_px_to_inches(layout.get("safe_left", 56)), _px_to_inches(margins.get("left", 56)))
    right = max(_px_to_inches(layout.get("safe_right", 56)), _px_to_inches(margins.get("right", 56)))
    top = max(_px_to_inches(layout.get("safe_top", 64)), _px_to_inches(margins.get("top", 56)))
    bottom = max(_px_to_inches(layout.get("safe_bottom", 48)), _px_to_inches(margins.get("bottom", 56)))
    
    width = prs.slide_width.inches - left - right
    height = prs.slide_height.inches - top - bottom
    
    return (left, top, width, height)


# --- Background Rendering --------------------------------------------------

def _background_image_bytes(theme: Dict[str, Any], width_px: int, height_px: int) -> bytes:
    """Render vertical gradient PNG matching theme background."""
    bg_grad = theme.get("background_gradient", (theme["colors"]["bg"], theme["colors"]["bg"]))
    color_a = _hex_to_rgb_int(bg_grad[0])
    color_b = _hex_to_rgb_int(bg_grad[1])

    img = Image.new("RGB", (max(1, width_px), max(1, height_px)), color_a)
    draw = ImageDraw.Draw(img)
    
    for y in range(height_px):
        t = y / max(1, height_px - 1)
        r = int(color_a[0] * (1 - t) + color_b[0] * t)
        g = int(color_a[1] * (1 - t) + color_b[1] * t)
        b = int(color_a[2] * (1 - t) + color_b[2] * t)
        draw.line([(0, y), (width_px, y)], fill=(r, g, b))

    # Vignette overlay
    vig = theme.get("vignette", {})
    strength = vig.get("strength", 0.0)
    if strength > 0.01:
        overlay = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        steps = 16
        for i in range(steps):
            alpha = int((i / steps) * 255 * strength * 0.6)
            inset = int((steps - i) * 6)
            od.rectangle([inset, inset, width_px - inset, height_px - inset], 
                        fill=(0, 0, 0, alpha))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    bio = BytesIO()
    img.save(bio, format="PNG", optimize=True)
    return bio.getvalue()


def _add_background(slide, prs: Presentation, theme: Dict[str, Any]):
    """Add gradient background image to slide."""
    try:
        px_w = int(round(prs.slide_width.inches * 96))
        px_h = int(round(prs.slide_height.inches * 96))
        bg_bytes = _background_image_bytes(theme, px_w, px_h)
        bio = BytesIO(bg_bytes)
        slide.shapes.add_picture(bio, Inches(0), Inches(0), 
                                width=prs.slide_width, height=prs.slide_height)
    except Exception:
        # Fallback to solid color
        try:
            bg_rgb = _hex_to_rgb_int(theme["colors"]["bg"])
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = RGBColor(*bg_rgb)
        except Exception:
            pass


# --- Text Helpers ----------------------------------------------------------

def _add_textbox(slide, left_in, top_in, width_in, height_in, text, font_name, 
                 font_size, color_rgb, bold=False, alignment=PP_ALIGN.LEFT, 
                 vertical_anchor=MSO_ANCHOR.TOP):
    """Add a text box with specified formatting."""
    tb = slide.shapes.add_textbox(Inches(left_in), Inches(top_in), 
                                  Inches(width_in), Inches(height_in))
    tf = tb.text_frame
    tf.text = text
    tf.word_wrap = True
    tf.vertical_anchor = vertical_anchor
    
    p = tf.paragraphs[0]
    p.alignment = alignment
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = RGBColor(*color_rgb)
    
    try:
        p.font.name = font_name
    except Exception:
        pass
    
    return tb


def _text_fits_width(text: str, font_size: float, max_width_in: float) -> bool:
    """Rough check if text fits in width (approximation)."""
    # More conservative estimate: average character width in inches
    # Using 0.5 for typical proportional fonts
    approx_width = len(text) * 0.5 * font_size / 72.0
    return approx_width <= max_width_in


# --- Slide Renderers -------------------------------------------------------

def _title_splash(prs: Presentation, plan: LecturePlan, theme: Dict[str, Any], sizes: Dict[str, float]):
    """Render title splash slide (page 1)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_background(slide, prs, theme)
    
    frame_left, frame_top, frame_w, frame_h = _get_safe_frame(prs, theme)
    
    # Title text preparation
    title_font = theme["fonts"].get("title", "Helvetica-Bold")
    text_rgb = _hex_to_rgb_int(theme["colors"]["text"])
    title_text = plan.topic
    
    # Adaptive font sizing - much more aggressive
    display_size = sizes["display"]
    while display_size > 18 and not _text_fits_width(title_text, display_size, frame_w * 0.75):
        display_size -= 2
    
    # Calculate ornament size based on actual text dimensions
    # Rough estimate: width needs padding, height based on font size
    text_width_estimate = len(title_text) * 0.6 * display_size / 72.0
    ornament_w = min(text_width_estimate * 1.3, frame_w * 0.85)
    ornament_h = (display_size / 72.0) * 2.2  # Height proportional to font size
    
    ornament_left = frame_left + (frame_w - ornament_w) / 2
    ornament_top = frame_top + (frame_h - ornament_h) / 2
    
    # Theme-specific ornament
    theme_key = theme.get("name", "minimalist")
    accent_rgb = _hex_to_rgb_int(theme["colors"]["accent"])
    
    if theme_key == "minimalist":
        ornament_fill = _blend_with_white(accent_rgb, 0.12)
    elif theme_key == "chalkboard":
        ornament_fill = _blend_with_white(accent_rgb, 0.25)
    else:  # corporate
        ornament_fill = _blend_with_white(accent_rgb, 0.15)
    
    ornament = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(ornament_left), Inches(ornament_top),
        Inches(ornament_w), Inches(ornament_h)
    )
    ornament.fill.solid()
    ornament.fill.fore_color.rgb = RGBColor(*ornament_fill)
    ornament.line.fill.background()
    
    # Title centered - use same dimensions as ornament
    # Ensure sufficient contrast between ornament and title text (important for chalkboard)
    title_color_rgb = text_rgb
    try:
        if _contrast_ratio(tuple(ornament_fill), tuple(text_rgb)) < 4.5:
            # Use dark background color (theme bg) for text when ornament is too light
            title_color_rgb = _hex_to_rgb_int(theme["colors"]["bg"])
    except Exception:
        title_color_rgb = text_rgb

    _add_textbox(
        slide,
        ornament_left,
        ornament_top,
        ornament_w,
        ornament_h,
        title_text,
        title_font,
        display_size,
        title_color_rgb,
        bold=True,
        alignment=PP_ALIGN.CENTER,
        vertical_anchor=MSO_ANCHOR.MIDDLE,
    )


def _content_slide(prs: Presentation, slide_item: SlideItem, theme: Dict[str, Any], 
                   sizes: Dict[str, float]) -> int:
    """Create slide(s) with heading + bullet points. Returns number of slides created."""
    points = slide_item.points or []
    if not points:
        return 0
    
    frame_left, frame_top, frame_w, frame_h = _get_safe_frame(prs, theme)
    
    # Compute max bullets per slide
    layout = theme.get("layout", {})
    body_size = sizes["body"]
    leading = body_size * layout.get("bullet_leading", 1.35)
    para_gap = layout.get("para_gap_pt", 10)
    
    line_h_in = (leading + para_gap) / 72.0
    available_h = frame_h - 1.5  # More space reserved for title
    max_bullets = max(4, int(available_h / line_h_in))
    
    created = 0
    start = 0
    
    while start < len(points):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        _add_background(slide, prs, theme)
        
        # Title band - with more top padding
        title_font = theme["fonts"].get("title", "Helvetica-Bold")
        text_rgb = _hex_to_rgb_int(theme["colors"]["text"])
        band_h = 1.0  # Increased height
        title_top = frame_top + 0.3  # Added top padding
        
        title_text = slide_item.title if created == 0 else f"{slide_item.title} (cont.)"
        
        _add_textbox(
            slide,
            frame_left,
            title_top,
            frame_w,
            band_h,
            title_text,
            title_font,
            sizes["title"],
            text_rgb,
            bold=True,
            alignment=PP_ALIGN.LEFT,
            vertical_anchor=MSO_ANCHOR.TOP
        )
        
        # Bullets area - starts lower to account for title padding
        bullets_top = title_top + band_h + 0.3  # More gap after title
        bullets_h = frame_h - (bullets_top - frame_top)
        
        tb = slide.shapes.add_textbox(
            Inches(frame_left), Inches(bullets_top),
            Inches(frame_w), Inches(bullets_h)
        )
        tf = tb.text_frame
        tf.clear()
        tf.word_wrap = True
        tf.margin_left = Inches(0.2)
        tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0)
        
        # Add bullets
        end = min(len(points), start + max_bullets)
        body_font = theme["fonts"].get("body", "Helvetica")
        theme_key = theme.get("name", "minimalist")
        
        for idx in range(start, end):
            ptext = points[idx]
            icon = get_point_icon(theme_key, idx - start)
            
            if idx == start:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            
            p.text = f"{icon} {ptext}"
            p.level = 0
            p.font.size = Pt(body_size)
            p.font.color.rgb = RGBColor(*text_rgb)
            p.font.name = body_font
            p.space_after = Pt(para_gap)
            p.line_spacing = leading / body_size
        
        start = end
        created += 1
    
    return created


# --- Footer ----------------------------------------------------------------

def _add_footer(slide, prs: Presentation, plan: LecturePlan, page_num: int, 
               total_pages: int, theme: Dict[str, Any], sizes: Dict[str, float]):
    """Add footer with page number and topic."""
    frame_left, frame_top, frame_w, frame_h = _get_safe_frame(prs, theme)
    layout = theme.get("layout", {})
    
    footer_y = prs.slide_height.inches - _px_to_inches(layout.get("safe_bottom", 48)) - 0.3
    
    # Divider line
    muted_rgb = _hex_to_rgb_int(theme["colors"]["muted"])
    divider = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(frame_left), Inches(footer_y),
        Inches(frame_w), Inches(0.01)
    )
    divider.fill.solid()
    divider.fill.fore_color.rgb = RGBColor(*muted_rgb)
    divider.line.fill.background()
    
    # Footer text
    footer_font = theme["fonts"].get("body", "Helvetica")
    folio = f"{plan.topic} • {page_num}/{total_pages}"
    
    # Theme-specific alignment
    theme_key = theme.get("name", "minimalist")
    if theme_key == "minimalist":
        align = PP_ALIGN.CENTER
    elif theme_key == "chalkboard":
        align = PP_ALIGN.LEFT
    else:  # corporate
        align = PP_ALIGN.RIGHT
    
    _add_textbox(
        slide,
        frame_left,
        footer_y + 0.05,
        frame_w,
        0.3,
        folio,
        footer_font,
        sizes["footer"],
        muted_rgb,
        alignment=align
    )


# --- Main Builder ----------------------------------------------------------

def build_pptx(plan: LecturePlan, theme: Optional[Dict[str, Any]] = None) -> bytes:
    """Build themed PPTX from LecturePlan - heading + bullets only."""
    theme = theme or get_theme(plan.theme)
    
    # Add theme name for icon helpers
    theme["name"] = (plan.theme or "minimalist").lower()
    
    prs = Presentation()
    _configure_slide_size(prs, plan)
    
    # Compute adaptive sizes
    sizes = _compute_scale_and_sizes(prs, theme)
    
    # Count total pages
    total_pages = 1  # Title splash
    for slide_item in plan.slides:
        points_count = len(slide_item.points or [])
        body_size = sizes["body"]
        leading = body_size * theme.get("layout", {}).get("bullet_leading", 1.35)
        para_gap = theme.get("layout", {}).get("para_gap_pt", 10)
        line_h_in = (leading + para_gap) / 72.0
        frame_left, frame_top, frame_w, frame_h = _get_safe_frame(prs, theme)
        available_h = frame_h - 1.2
        max_bullets = max(4, int(available_h / line_h_in))
        total_pages += math.ceil(points_count / max_bullets)
    
    page_num = 0
    
    # Title splash
    _title_splash(prs, plan, theme, sizes)
    page_num += 1
    _add_footer(prs.slides[page_num - 1], prs, plan, page_num, total_pages, theme, sizes)
    
    # Content slides (heading + bullets only)
    for slide_item in plan.slides:
        slides_created = _content_slide(prs, slide_item, theme, sizes)
        for i in range(slides_created):
            page_num += 1
            _add_footer(prs.slides[page_num - 1], prs, plan, page_num, total_pages, theme, sizes)
    
    # Save to bytes
    out = BytesIO()
    prs.save(out)
    out.seek(0)
    return out.getvalue()