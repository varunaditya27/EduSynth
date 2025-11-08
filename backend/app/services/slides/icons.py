"""
Unicode icon provider for themed PDF content.
"""
from typing import Dict, List


# Icon sets for each theme
THEME_ICONS: Dict[str, List[str]] = {
    "minimalist": ["•", "◦", "▹", "▸", "▫", "▪"],
    "chalkboard": ["✦", "✧", "—", "∙", "※", "⁕"],
    "corporate": ["■", "▪", "▸", "▹", "▫", "□"],
}

# Spacing between points in lecture notes (in points)
POINT_SPACING_PT: int = 10


def get_point_icon(theme_key: str, index: int) -> str:
    """
    Get a unicode icon for a bullet point based on theme and index.
    
    Args:
        theme_key: Theme identifier (minimalist, chalkboard, corporate)
        index: Point index (rotates through icon set)
        
    Returns:
        Unicode character as string
    """
    theme_lower = theme_key.lower()
    
    # Get icon set for theme (default to minimalist)
    icons = THEME_ICONS.get(theme_lower, THEME_ICONS["minimalist"])
    
    # Rotate through icons
    return icons[index % len(icons)]


def get_section_icon(theme_key: str, section_type: str) -> str:
    """
    Get special icons for section headers.
    
    Args:
        theme_key: Theme identifier
        section_type: Type of section (mindmap, flowchart, notes)
        
    Returns:
        Unicode icon character
    """
    section_icons = {
        "mindmap": "📊",
        "flowchart": "🔄",
        "notes": "📝",
        "summary": "📋",
        "reference": "🔖",
    }
    
    return section_icons.get(section_type, "●")


def get_decorative_border(theme_key: str, length: int = 40) -> str:
    """
    Generate a decorative text border for theme.
    
    Args:
        theme_key: Theme identifier
        length: Character length of border
        
    Returns:
        Decorative border string
    """
    theme_lower = theme_key.lower()
    
    border_chars = {
        "minimalist": "─",
        "chalkboard": "~",
        "corporate": "═",
    }
    
    char = border_chars.get(theme_lower, "─")
    return char * length