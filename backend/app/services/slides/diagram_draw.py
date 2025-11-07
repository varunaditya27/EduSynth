"""
Pillow-based diagram utilities for enhanced PDF visuals.
"""
from io import BytesIO
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas


def radial_gradient_png(
    size: Tuple[int, int],
    inner: str,
    outer: str
) -> bytes:
    """
    Generate a radial gradient as PNG bytes.
    
    Args:
        size: (width, height) in pixels
        inner: Inner color hex string (e.g., "#4A90E2")
        outer: Outer color hex string (e.g., "#FFFFFF")
        
    Returns:
        PNG image bytes
    """
    width, height = size
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Parse colors
    inner_rgb = hex_to_rgb(inner)
    outer_rgb = hex_to_rgb(outer)
    
    center_x, center_y = width // 2, height // 2
    max_radius = min(width, height) // 2
    
    # Draw concentric circles with interpolated colors
    steps = 50
    for i in range(steps, 0, -1):
        ratio = i / steps
        radius = int(max_radius * ratio)
        
        # Interpolate color
        r = int(outer_rgb[0] + (inner_rgb[0] - outer_rgb[0]) * ratio)
        g = int(outer_rgb[1] + (inner_rgb[1] - outer_rgb[1]) * ratio)
        b = int(outer_rgb[2] + (inner_rgb[2] - outer_rgb[2]) * ratio)
        alpha = int(255 * (0.3 + 0.7 * ratio))  # Fade out at edges
        
        bbox = [
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
        ]
        draw.ellipse(bbox, fill=(r, g, b, alpha))
    
    # Save to bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()


def node_bubble_png(
    text: str,
    fill_hex: str,
    text_hex: str,
    size: Tuple[int, int] = (120, 60)
) -> bytes:
    """
    Generate a rounded bubble with text as PNG.
    
    Args:
        text: Text to display
        fill_hex: Bubble fill color hex
        text_hex: Text color hex
        size: (width, height) in pixels
        
    Returns:
        PNG image bytes
    """
    width, height = size
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Parse colors
    fill_rgb = hex_to_rgb(fill_hex)
    text_rgb = hex_to_rgb(text_hex)
    
    # Draw rounded rectangle (ellipse approximation)
    corner_radius = min(width, height) // 4
    draw.rounded_rectangle(
        [(0, 0), (width - 1, height - 1)],
        radius=corner_radius,
        fill=(*fill_rgb, 255)
    )
    
    # Draw text (centered)
    try:
        font = ImageFont.truetype("Arial", size=14)
    except:
        font = ImageFont.load_default()
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    
    draw.text((text_x, text_y), text, fill=(*text_rgb, 255), font=font)
    
    # Save to bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color string to RGB tuple.
    
    Args:
        hex_color: Color in hex format (e.g., "#4A90E2" or "4A90E2")
        
    Returns:
        (r, g, b) tuple with values 0-255
    """
    hex_color = hex_color.lstrip("#")
    
    if len(hex_color) == 3:
        # Short form: #RGB -> #RRGGBB
        hex_color = "".join([c * 2 for c in hex_color])
    
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def measure_text(c: canvas.Canvas, text: str, font_name: str, font_size: float) -> float:
    """
    Measure the width of text in points.
    
    Args:
        c: ReportLab canvas
        text: Text to measure
        font_name: Font name (e.g., "Helvetica-Bold")
        font_size: Font size in points
        
    Returns:
        Text width in points
    """
    return c.stringWidth(text, font_name, font_size)


def rounded_rect(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    radius: float,
    fill: bool = True,
    stroke: bool = False
) -> None:
    """
    Draw a rounded rectangle on the canvas.
    
    Args:
        c: ReportLab canvas
        x: Bottom-left x coordinate
        y: Bottom-left y coordinate
        width: Rectangle width
        height: Rectangle height
        radius: Corner radius
        fill: Whether to fill the shape
        stroke: Whether to stroke the outline
    """
    # Clamp radius
    radius = min(radius, width / 2, height / 2)
    
    path = c.beginPath()
    
    # Start at top-left corner (after curve)
    path.moveTo(x + radius, y + height)
    
    # Top edge
    path.lineTo(x + width - radius, y + height)
    
    # Top-right corner
    path.arcTo(
        x + width - 2 * radius, y + height - 2 * radius,
        x + width, y + height,
        startAng=0, extent=90
    )
    
    # Right edge
    path.lineTo(x + width, y + radius)
    
    # Bottom-right corner
    path.arcTo(
        x + width - 2 * radius, y,
        x + width, y + 2 * radius,
        startAng=270, extent=90
    )
    
    # Bottom edge
    path.lineTo(x + radius, y)
    
    # Bottom-left corner
    path.arcTo(
        x, y,
        x + 2 * radius, y + 2 * radius,
        startAng=180, extent=90
    )
    
    # Left edge
    path.lineTo(x, y + height - radius)
    
    # Top-left corner
    path.arcTo(
        x, y + height - 2 * radius,
        x + 2 * radius, y + height,
        startAng=90, extent=90
    )
    
    path.close()
    
    c.drawPath(path, stroke=1 if stroke else 0, fill=1 if fill else 0)