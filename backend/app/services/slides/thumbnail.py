"""
Cover thumbnail renderer using Pillow.
"""
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Dict, Any
import random

# diagram_draw.hex_to_rgb returns normalized floats (0..1). For Pillow we need 0..255 ints.


def _hex_to_rgb_int(hex_color: str):
    hc = (hex_color or "#000000").lstrip("#")
    if len(hc) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    return tuple(int(hc[i : i + 2], 16) for i in (0, 2, 4))


def render_cover_thumbnail(
    topic: str, 
    theme: Dict[str, Any], 
    size: Tuple[int, int] = (1280, 720)
) -> bytes:
    """
    Render a cover thumbnail with gradient background and styled title.
    
    Args:
        topic: Lecture topic text
        theme: Theme token dictionary
        size: Image dimensions (width, height)
        
    Returns:
        PNG image bytes
    """
    width, height = size

    # Supersample rendering for crisp text and gradients (render at 2x and downscale)
    SS = 2
    big_w = width * SS
    big_h = height * SS

    # Create high-res base image
    img = Image.new("RGB", (big_w, big_h), color=_hex_to_rgb_int(theme["colors"]["bg"]))
    draw = ImageDraw.Draw(img, "RGBA")

    # Draw gradient background (vertical)
    gradient_stops = theme.get("background_gradient", (theme["colors"]["bg"], theme["colors"].get("paper", theme["colors"]["bg"])))
    color1 = _hex_to_rgb_int(gradient_stops[0])
    color2 = _hex_to_rgb_int(gradient_stops[1])

    for y in range(big_h):
        ratio = y / max(1, big_h - 1)
        r = int(round(color1[0] * (1 - ratio) + color2[0] * ratio))
        g = int(round(color1[1] * (1 - ratio) + color2[1] * ratio))
        b = int(round(color1[2] * (1 - ratio) + color2[2] * ratio))
        draw.line([(0, y), (big_w, y)], fill=(r, g, b))

    # Add subtle noise overlay for depth
    noise_layer = Image.new("RGBA", (big_w, big_h), (0, 0, 0, 0))
    noise_draw = ImageDraw.Draw(noise_layer)
    for _ in range(4000):
        x = random.randint(0, max(0, big_w - 1))
        y = random.randint(0, max(0, big_h - 1))
        alpha = random.randint(4, 12)
        noise_draw.point((x, y), fill=(255, 255, 255, alpha))
    img.paste(noise_layer, (0, 0), noise_layer)

    # Draw accent bar at top (scaled)
    accent_color = _hex_to_rgb_int(theme["colors"]["accent"])
    bar_height = int(8 * SS)
    draw.rectangle([(0, 0), (big_w, bar_height)], fill=accent_color)

    # Load font with fallback and scale title size based on image width for parity
    base_width = 1280
    scale = max(0.6, min(1.6, width / base_width))
    # prefer display size for big cover, fall back to title
    theme_display = theme.get("sizes", {}).get("display") or theme.get("sizes", {}).get("title", 36)
    title_size = int(theme_display * 1.0 * scale * SS)
    font_name = theme.get("fonts", {}).get("title")
    # Prefer an installed TTF; fallback to DejaVuSans which PIL typically ships with
    try:
        if font_name and isinstance(font_name, str) and font_name.endswith('.ttf'):
            font = ImageFont.truetype(font_name, title_size)
        else:
            # Try common bundled font
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", title_size)
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", title_size)
        except Exception:
            font = ImageFont.load_default()

    # Wrap text if too long (measure on high-res canvas)
    words = topic.split()
    lines = []
    current_line = []
    max_line_width = int(big_w * 0.8)
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > max_line_width:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
        else:
            current_line.append(word)
    if current_line:
        lines.append(" ".join(current_line))

    # Draw title centered (on supersampled canvas)
    text_color = _hex_to_rgb_int(theme["colors"]["text"])
    line_h = title_size + int(10 * SS)
    total_height = len(lines) * line_h
    start_y = (big_h - total_height) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (big_w - text_width) // 2
        y = start_y + i * line_h

        # Draw text shadow for depth (supersampled)
        shadow_offset = int(3 * SS)
        shadow_color = (*text_color[:3], 120)
        draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=shadow_color)

        # Draw main text
        draw.text((x, y), line, font=font, fill=text_color)

    # Draw accent bar at bottom (scaled)
    draw.rectangle([(0, big_h - bar_height), (big_w, big_h)], fill=accent_color)

    # Downscale to requested size for crisp result
    final = img.resize((width, height), resample=Image.LANCZOS)

    # Convert to PNG bytes
    buffer = BytesIO()
    final.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()