"""
PDF Builder for EduSynth Slide Decks
Generates beautiful cheat-sheets + lecture notes from LecturePlan
"""
from io import BytesIO
from typing import List, Tuple, Optional
import math

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.schemas.slides import LecturePlan, SlideItem
from .icons import get_point_icon, POINT_SPACING_PT
from .diagram_draw import radial_gradient_png, measure_text, rounded_rect


def build_pdf(plan: LecturePlan, theme: dict, cheatsheet_only: bool = False, notes_only: bool = False) -> bytes:
    """
    Build a complete PDF with cheat-sheet and lecture notes.
    
    Args:
        plan: Lecture plan with slides
        theme: Theme tokens (colors, fonts, sizes)
        cheatsheet_only: Only render cheat-sheet pages (mindmap + flowchart)
        notes_only: Only render lecture notes pages
        
    Returns:
        PDF as bytes
    """
    buffer = BytesIO()
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    
    if not notes_only:
        # Page 1: Mindmap
        draw_mindmap_v2(c, plan, theme, page_width, page_height)
        c.showPage()
        
        # Page 2: Flowchart
        draw_flowchart_v2(c, plan, theme, page_width, page_height)
        c.showPage()
    
    if not cheatsheet_only:
        # Lecture Notes: one page per slide
        for idx, slide in enumerate(plan.slides, start=1):
            draw_notes_page(c, slide, idx, len(plan.slides), plan, theme, page_width, page_height)
            c.showPage()
    
    c.save()
    buffer.seek(0)
    return buffer.read()


class Bubble:
    """Represents a bubble with position and dimensions for collision detection."""
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def intersects(self, other: 'Bubble') -> bool:
        """Check if this bubble intersects with another."""
        # Use circular approximation for collision
        radius1 = max(self.width, self.height) / 2
        radius2 = max(other.width, other.height) / 2
        distance = math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
        return distance < (radius1 + radius2 + 10)  # 10px buffer


def draw_mindmap_v2(
    c: canvas.Canvas,
    plan: LecturePlan,
    theme: dict,
    page_width: float,
    page_height: float
) -> None:
    """
    Draw radial mindmap v2: center bubble with evenly spaced branches and sub-bubbles.
    """
    # Background gradient
    bg_color = theme["colors"]["bg"]
    accent_color = theme["colors"]["accent"]
    
    center_x = page_width / 2
    center_y = page_height / 2
    
    # Draw subtle radial gradient background
    for i in range(15, 0, -1):
        alpha = 0.03 + (i * 0.015)
        ring_color = HexColor(accent_color)
        c.setFillColorRGB(ring_color.red, ring_color.green, ring_color.blue, alpha=min(alpha, 0.2))
        radius = i * 20
        c.circle(center_x, center_y, radius, fill=1, stroke=0)
    
    # Calculate branch radius (35% of min dimension)
    branch_radius = min(page_width, page_height) * 0.35
    
    # Center bubble
    topic_text = plan.topic
    topic_font_size = theme["sizes"]["title"]
    topic_width = measure_text(c, topic_text, "Helvetica-Bold", topic_font_size)
    center_bubble_width = topic_width + 40
    center_bubble_height = topic_font_size + 30
    
    c.setFillColor(HexColor(accent_color))
    rounded_rect(c, center_x - center_bubble_width / 2, center_y - center_bubble_height / 2, 
                 center_bubble_width, center_bubble_height, 15, fill=True)
    
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", topic_font_size)
    c.drawString(center_x - topic_width / 2, center_y - topic_font_size / 3, topic_text)
    
    # Branch layout
    main_slides = plan.slides[:8]
    num_spokes = len(main_slides)
    
    placed_bubbles: List[Bubble] = [Bubble(center_x, center_y, center_bubble_width, center_bubble_height)]
    
    accent_color2 = HexColor(theme["colors"]["accent2"])
    text_color = HexColor(theme["colors"]["text"])
    
    for i, slide in enumerate(main_slides):
        base_angle = (2 * math.pi * i / num_spokes) - (math.pi / 2)
        
        # Collision avoidance: try up to 6 angle adjustments
        angle = base_angle
        bubble_placed = False
        
        for attempt in range(6):
            node_x = center_x + branch_radius * math.cos(angle)
            node_y = center_y + branch_radius * math.sin(angle)
            
            # Measure bubble size
            title_text = slide.title[:25] + "..." if len(slide.title) > 25 else slide.title
            title_width = measure_text(c, title_text, "Helvetica-Bold", 14)
            bubble_width = title_width + 30
            bubble_height = 50
            
            test_bubble = Bubble(node_x, node_y, bubble_width, bubble_height)
            
            # Check collision
            has_collision = any(test_bubble.intersects(b) for b in placed_bubbles)
            
            if not has_collision:
                bubble_placed = True
                placed_bubbles.append(test_bubble)
                break
            
            # Nudge angle
            angle = base_angle + (attempt + 1) * (7 * math.pi / 180) * (1 if attempt % 2 == 0 else -1)
        
        if not bubble_placed:
            # Force placement if all attempts fail
            node_x = center_x + branch_radius * math.cos(angle)
            node_y = center_y + branch_radius * math.sin(angle)
            title_text = slide.title[:25] + "..." if len(slide.title) > 25 else slide.title
            title_width = measure_text(c, title_text, "Helvetica-Bold", 14)
            bubble_width = title_width + 30
            bubble_height = 50
        
        # Draw Bezier connector from center to branch
        c.setStrokeColor(HexColor(accent_color))
        c.setLineWidth(2.5)
        
        # Control points for smooth curve
        ctrl_distance = branch_radius * 0.4
        ctrl1_x = center_x + ctrl_distance * math.cos(angle)
        ctrl1_y = center_y + ctrl_distance * math.sin(angle)
        ctrl2_x = node_x - ctrl_distance * 0.3 * math.cos(angle)
        ctrl2_y = node_y - ctrl_distance * 0.3 * math.sin(angle)
        
        path = c.beginPath()
        path.moveTo(center_x, center_y)
        path.curveTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, node_x, node_y)
        c.drawPath(path, stroke=1, fill=0)
        
        # Draw branch bubble (alternating colors)
        fill_color = accent_color2 if i % 2 == 0 else HexColor(accent_color)
        c.setFillColor(fill_color)
        rounded_rect(c, node_x - bubble_width / 2, node_y - bubble_height / 2,
                     bubble_width, bubble_height, 12, fill=True)
        
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(node_x - title_width / 2, node_y - 5, title_text)
        
        # Draw sub-bubbles (up to 2 points)
        points_to_show = slide.points[:2]
        for j, point in enumerate(points_to_show):
            # Offset along branch angle
            sub_distance = branch_radius + 90 + (j * 40)
            sub_x = center_x + sub_distance * math.cos(angle)
            sub_y = center_y + sub_distance * math.sin(angle)
            
            point_text = point[:18] + "..." if len(point) > 18 else point
            point_width = measure_text(c, point_text, "Helvetica", 10)
            sub_width = point_width + 20
            sub_height = 35
            
            # Small bubble
            c.setFillColor(HexColor(theme["colors"]["muted"]))
            rounded_rect(c, sub_x - sub_width / 2, sub_y - sub_height / 2,
                         sub_width, sub_height, 8, fill=True)
            
            c.setFillColor(text_color)
            c.setFont("Helvetica", 10)
            c.drawString(sub_x - point_width / 2, sub_y - 3, point_text)
    
    # Title
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, page_height - 50, "📊 Knowledge Map")


def draw_flowchart_v2(
    c: canvas.Canvas,
    plan: LecturePlan,
    theme: dict,
    page_width: float,
    page_height: float
) -> None:
    """
    Draw linear flowchart v2 with auto-sized boxes and consistent spacing.
    """
    # Find process slide
    process_slide: Optional[SlideItem] = None
    for slide in plan.slides:
        if hasattr(slide, 'diagram') and slide.diagram == "process":
            process_slide = slide
            break
    
    if not process_slide and plan.slides:
        process_slide = plan.slides[0]
    
    if not process_slide:
        return
    
    # Background
    c.setFillColor(HexColor(theme["colors"]["bg"]))
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    
    # Title
    text_color = HexColor(theme["colors"]["text"])
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, page_height - 50, "🔄 Process Flow")
    
    # Get steps (3-6 points)
    steps = process_slide.points[:6]
    num_steps = len(steps)
    
    if num_steps == 0:
        return
    
    # Calculate box sizes
    box_heights = 85
    box_widths: List[float] = []
    max_box_width = 160
    
    for step in steps:
        step_text = step[:50] + "..." if len(step) > 50 else step
        text_width = measure_text(c, step_text, "Helvetica", 11)
        box_width = min(max(text_width + 30, 120), max_box_width)
        box_widths.append(box_width)
    
    # Calculate spacing
    total_box_width = sum(box_widths)
    arrow_spacing = 40
    total_arrows = (num_steps - 1) * arrow_spacing
    available_width = page_width - 100
    
    if total_box_width + total_arrows > available_width:
        # Scale down boxes
        scale_factor = (available_width - total_arrows) / total_box_width
        box_widths = [w * scale_factor for w in box_widths]
    
    start_x = (page_width - sum(box_widths) - total_arrows) / 2
    y_position = page_height / 2
    
    accent_color = HexColor(theme["colors"]["accent"])
    accent2_color = HexColor(theme["colors"]["accent2"])
    
    current_x = start_x
    
    for i, step in enumerate(steps):
        box_width = box_widths[i]
        
        # Draw rounded box
        c.setFillColor(accent_color)
        rounded_rect(c, current_x, y_position - box_heights / 2,
                     box_width, box_heights, 12, fill=True)
        
        # Step number
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(current_x + 12, y_position + 18, f"Step {i + 1}")
        
        # Wrap text
        c.setFont("Helvetica", 11)
        step_text = step[:50] + "..." if len(step) > 50 else step
        words = step_text.split()
        lines: List[str] = []
        current_line: List[str] = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            if measure_text(c, test_line, "Helvetica", 11) < box_width - 24:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        # Draw lines (max 3)
        for j, line in enumerate(lines[:3]):
            c.drawString(current_x + 12, y_position - 5 - j * 14, line)
        
        # Draw arrow to next
        if i < num_steps - 1:
            arrow_start_x = current_x + box_width
            arrow_end_x = arrow_start_x + arrow_spacing
            arrow_y = y_position
            
            c.setStrokeColor(accent2_color)
            c.setFillColor(accent2_color)
            c.setLineWidth(3)
            c.line(arrow_start_x, arrow_y, arrow_end_x - 10, arrow_y)
            
            # Arrowhead
            path = c.beginPath()
            path.moveTo(arrow_end_x, arrow_y)
            path.lineTo(arrow_end_x - 10, arrow_y - 6)
            path.lineTo(arrow_end_x - 10, arrow_y + 6)
            path.close()
            c.drawPath(path, stroke=0, fill=1)
            
            current_x = arrow_end_x
        else:
            current_x += box_width


def draw_notes_page(
    c: canvas.Canvas,
    slide: SlideItem,
    idx: int,
    total: int,
    plan: LecturePlan,
    theme: dict,
    page_width: float,
    page_height: float
) -> None:
    """
    Draw one lecture notes page with expanded slide content.
    """
    # Background
    c.setFillColor(HexColor(theme["colors"]["bg"]))
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    
    # Top accent header bar
    accent_color = HexColor(theme["colors"]["accent"])
    c.setFillColor(accent_color)
    c.rect(0, page_height - 80, page_width, 80, fill=1, stroke=0)
    
    # Slide title in header
    c.setFillColor(white)
    title_size = theme["sizes"].get("title", 28)
    c.setFont("Helvetica-Bold", title_size)
    c.drawString(100, page_height - 50, slide.title)
    
    # Slide number
    c.setFont("Helvetica", 14)
    c.drawString(100, page_height - 70, f"Slide {idx} of {total}")
    
    # Left sidebar
    muted_color = HexColor(theme["colors"]["muted"])
    c.setFillColor(muted_color)
    c.rect(0, 0, 80, page_height - 80, fill=1, stroke=0)
    
    # Content area
    content_x = 100
    content_y = page_height - 120
    max_content_width = page_width - 140  # Clamped width for better wrapping
    
    text_color = HexColor(theme["colors"]["text"])
    c.setFillColor(text_color)
    body_size = theme["sizes"].get("body", 14)
    
    # Draw each point
    y_offset = content_y
    
    for point_idx, point in enumerate(slide.points):
        # Icon with consistent spacing
        icon = get_point_icon(plan.theme, point_idx)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(content_x, y_offset, icon)
        
        # Expand point
        expanded_text = expand_point(point)
        
        # Word wrap
        c.setFont("Helvetica", body_size)
        words = expanded_text.split()
        lines: List[str] = []
        current_line: List[str] = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            if measure_text(c, test_line, "Helvetica", body_size) < max_content_width - 40:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        # Draw wrapped text
        for line in lines:
            c.drawString(content_x + 30, y_offset, line)
            y_offset -= 20
            
            if y_offset < 100:
                break
        
        y_offset -= POINT_SPACING_PT
        
        if y_offset < 100:
            break
    
    # Footer with page number
    footer_size = theme["sizes"].get("footer", 10)
    c.setFont("Helvetica", footer_size)
    c.setFillColor(HexColor(theme["colors"]["muted"]))
    
    page_num = idx + 2  # +2 for cheat-sheet pages
    total_pages = total + 2
    
    if plan.theme.lower() == "corporate":
        footer_text = f"{plan.topic} — {page_num}/{total_pages}"
    else:
        footer_text = f"Page {page_num}"
    
    c.drawString(page_width / 2 - 50, 30, footer_text)


def expand_point(point: str) -> str:
    """
    Expand a bullet point into a short paragraph (2-3 sentences).
    """
    expansions = [
        f"{point}. This concept is fundamental to understanding the overall topic.",
        f"{point}. Let's explore this idea in more detail.",
        f"{point}. This plays a crucial role in the broader context.",
        f"{point}. Understanding this helps build a strong foundation.",
        f"{point}. This element connects directly to our main objectives.",
    ]
    
    import random
    return random.choice(expansions)