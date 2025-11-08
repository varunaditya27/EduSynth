from __future__ import annotations

def _base_sizes():
    return {
        "display": 46,
        "title": 38,
        "h2": 28,
        "h3": 22,
        "body": 14,
        "caption": 11,
        "code": 12,
        "footer": 10,
    }

def _base_radius():
    return {"sm": 6, "md": 12, "lg": 18}

def _base_layout():
    return {
        "safe_top": 64,
        "safe_bottom": 48,   # footer band height
        "safe_left": 56,
        "safe_right": 56,
        "title_min_size": 18,
        "bullet_leading": 1.35,  # multiplier on body font size
        "para_gap_pt": 10,
        "bullet_indent_pt": 20,
    }

def _base_margins():
    # standard page margins (used alongside safe_* bands)
    return {"top": 56, "right": 56, "bottom": 56, "left": 56}

def _base_fonts_minimal():
    return {
        "title": "Helvetica-Bold",
        "body": "Helvetica",
        "mono": "Courier",
        "fallback_title": "Helvetica-Bold",
        "fallback_body": "Helvetica",
    }

def _base_fonts_chalk():
    # Use Helvetica variants as safe fallback (no external font files)
    return {
        "title": "Helvetica-Bold",
        "body": "Helvetica",
        "mono": "Courier",
        "fallback_title": "Helvetica-Bold",
        "fallback_body": "Helvetica",
    }

def _base_fonts_corporate():
    return {
        "title": "Helvetica-Bold",
        "body": "Helvetica",
        "mono": "Courier",
        "fallback_title": "Helvetica-Bold",
        "fallback_body": "Helvetica",
    }

def get_theme(key: str) -> dict:
    key = (key or "minimalist").lower()

    if key == "chalkboard":
        return {
            "fonts": _base_fonts_chalk(),
            "sizes": _base_sizes(),
            "radius": _base_radius(),
            "layout": _base_layout(),
            "margins": _base_margins(),
            "colors": {
                "bg": "#1F3D2B",
                "paper": "#233F2E",
                "text": "#F1F5F9",
                "muted": "#A7B3A9",
                "accent": "#FFD700",
                "accent2": "#FF6B9D",
                "success": "#10B981",
                "warn": "#F59E0B",
                "danger": "#EF4444",
            },
            "background_gradient": ("#1F3D2B", "#274E37"),
            "vignette": {"strength": 0.10},
            "cheatsheet": {
                "mindmap_radius_pct": 0.35,
                "sub_radius_offset": [70, 120],
                "max_branches": 10,
            },
        }

    if key == "corporate":
        return {
            "fonts": _base_fonts_corporate(),
            "sizes": _base_sizes(),
            "radius": _base_radius(),
            "layout": _base_layout(),
            "margins": _base_margins(),
            "colors": {
                "bg": "#F4F7FB",
                "paper": "#FFFFFF",
                "text": "#0F172A",
                "muted": "#64748B",
                "accent": "#2563EB",  # blue
                "accent2": "#DC2626", # red
                "success": "#10B981",
                "warn": "#F59E0B",
                "danger": "#EF4444",
            },
            "background_gradient": ("#F8FAFC", "#EAF2FF"),
            "vignette": {"strength": 0.08},
            "cheatsheet": {
                "mindmap_radius_pct": 0.35,
                "sub_radius_offset": [70, 120],
                "max_branches": 10,
            },
        }

    # minimalist (default)
    return {
        "fonts": _base_fonts_minimal(),
        "sizes": _base_sizes(),
        "radius": _base_radius(),
        "layout": _base_layout(),
        "margins": _base_margins(),
        "colors": {
            "bg": "#FFFFFF",
            "paper": "#FFFFFF",
            "text": "#0B1220",
            "muted": "#6B7280",
            "accent": "#2563EB",  # blue
            "accent2": "#10B981", # green
            "success": "#10B981",
            "warn": "#F59E0B",
            "danger": "#EF4444",
        },
        "background_gradient": ("#FFFFFF", "#EEF2F7"),
        "vignette": {"strength": 0.06},
        "cheatsheet": {
            "mindmap_radius_pct": 0.35,
            "sub_radius_offset": [70, 120],
            "max_branches": 10,
        },
    }
