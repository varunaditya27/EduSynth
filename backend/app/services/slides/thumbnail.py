"""
Cover thumbnail renderer using Pillow.
"""
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Dict, Any
import random

from .theme_tokens import hex_to_rgb


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
    
    # Create base image
    img = Image.new("RGB", size, color=hex_to_rgb(theme["colors"]["bg"]))
    draw = ImageDraw.Draw(img, "RGBA")
    
    # Draw gradient background
    gradient_stops = theme["background_gradient"]
    color1 = hex_to_rgb(gradient_stops[0])
    color2 = hex_to_rgb(gradient_stops[1])
    
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Add subtle noise overlay for depth
    noise_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    noise_draw = ImageDraw.Draw(noise_layer)
    for _ in range(1000):
        x = random.randint(0, width)
        y = random.randint(0, height)
        alpha = random.randint(5, 15)
        noise_draw.point((x, y), fill=(255, 255, 255, alpha))
    img.paste(noise_layer, (0, 0), noise_layer)
    
    # Draw accent bar at top
    accent_color = hex_to_rgb(theme["colors"]["accent"])
    bar_height = 8
    draw.rectangle([(0, 0), (width, bar_height)], fill=accent_color)
    
    # Load font with fallback
    title_size = int(theme["sizes"]["title"] * 1.8)
    try:
        font = ImageFont.truetype(theme["fonts"]["title"], title_size)
    except:
        try:
            font = ImageFont.truetype(theme["fonts"]["title_fallback"], title_size)
        except:
            font = ImageFont.load_default()
    
    # Wrap text if too long
    words = topic.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > width * 0.8:
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
    
    # Draw title centered
    text_color = hex_to_rgb(theme["colors"]["text"])
    total_height = len(lines) * (title_size + 10)
    start_y = (height - total_height) // 2
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = start_y + i * (title_size + 10)
        
        # Draw text shadow for depth
        shadow_offset = 3
        shadow_color = (*text_color[:3], 100)
        draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=shadow_color)
        
        # Draw main text
        draw.text((x, y), line, font=font, fill=text_color)
    
    # Draw accent bar at bottom
    draw.rectangle([(0, height - bar_height), (width, height)], fill=accent_color)
    
    # Convert to PNG bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()