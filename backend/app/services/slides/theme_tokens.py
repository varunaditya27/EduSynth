"""
Theme token system for slide deck styling.
"""
from typing import Dict, Any, Tuple


THEMES: Dict[str, Dict[str, Any]] = {
    "minimalist": {
        "fonts": {
            "title": "Inter Semibold",
            "title_fallback": "Segoe UI Semibold",
            "body": "Inter",
            "body_fallback": "Segoe UI",
        },
        "sizes": {
            "title": 44,
            "subtitle": 24,
            "body": 24,
            "footer": 12,
        },
        "colors": {
            "bg": "#FFFFFF",
            "text": "#0F172A",
            "muted": "#64748B",
            "accent": "#2563EB",
            "accent2": "#10B981",
        },
        "margins_in": {
            "top": 1.0,
            "right": 1.0,
            "bottom": 1.0,
            "left": 1.0,
        },
        "bullet": "dot",
        "depth": {
            "shape_shadow_opacity": 0.25,
            "shape_shadow_offset_pt": 3,
        },
        "background_gradient": ("#FFFFFF", "#E2E8F0"),
        "header_bar": False,
        "footer": False,
    },
    "chalkboard": {
        "fonts": {
            "title": "Cabin Sketch",
            "title_fallback": "Arial Black",
            "body": "Comic Neue",
            "body_fallback": "Arial",
        },
        "sizes": {
            "title": 44,
            "subtitle": 24,
            "body": 24,
            "footer": 12,
        },
        "colors": {
            "bg": "#1F3D2B",
            "text": "#F1F5F9",
            "muted": "#CBD5E1",
            "accent": "#FBBF24",
            "accent2": "#34D399",
        },
        "margins_in": {
            "top": 1.0,
            "right": 1.0,
            "bottom": 1.0,
            "left": 1.0,
        },
        "bullet": "dash",
        "depth": {
            "shape_shadow_opacity": 0.25,
            "shape_shadow_offset_pt": 3,
        },
        "background_gradient": ("#1F3D2B", "#274E37"),
        "header_bar": False,
        "footer": False,
    },
    "corporate": {
        "fonts": {
            "title": "Source Sans Pro Semibold",
            "title_fallback": "Segoe UI Semibold",
            "body": "Source Sans Pro",
            "body_fallback": "Segoe UI",
        },
        "sizes": {
            "title": 40,
            "subtitle": 24,
            "body": 22,
            "footer": 12,
        },
        "colors": {
            "bg": "#F8FAFC",
            "text": "#0B132B",
            "muted": "#334155",
            "accent": "#3B82F6",
            "accent2": "#0EA5E9",
        },
        "margins_in": {
            "top": 1.0,
            "right": 1.0,
            "bottom": 1.0,
            "left": 1.0,
        },
        "bullet": "square",
        "depth": {
            "shape_shadow_opacity": 0.25,
            "shape_shadow_offset_pt": 3,
        },
        "background_gradient": ("#FFFFFF", "#E6F0FF"),
        "header_bar": True,
        "header_bar_height_px": 90,
        "footer": True,
    },
}


def get_theme(theme_key: str) -> Dict[str, Any]:
    """
    Get theme tokens by key.
    
    Args:
        theme_key: Theme identifier (minimalist, chalkboard, corporate)
        
    Returns:
        Theme token dictionary
        
    Raises:
        ValueError: If theme key is invalid
    """
    theme_key = theme_key.lower()
    if theme_key not in THEMES:
        # Default to minimalist
        return THEMES["minimalist"]
    return THEMES[theme_key]


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color to RGB tuple.
    
    Args:
        hex_color: Hex color string (e.g., "#FFFFFF")
        
    Returns:
        RGB tuple (0-255 range)
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_bullet_char(bullet_type: str) -> str:
    """
    Get bullet character for type.
    
    Args:
        bullet_type: Bullet type (dot, dash, square)
        
    Returns:
        Bullet character
    """
    bullet_chars = {
        "dot": "•",
        "dash": "–",
        "square": "■",
    }
    return bullet_chars.get(bullet_type, "•")