from __future__ import annotations

# Keep your existing rotations; add a semantic helper fallback-safe.

POINT_SPACING_PT = 12

THEME_BULLETS = {
    "minimalist": ["•", "◦", "▹"],
    "chalkboard": ["✦", "✧", "—"],
    "corporate":  ["■", "▪", "▸"],
}

SEMANTIC = [
    (("time","timeline","duration"), "⏱"),
    (("compare","vs","contrast"), "⚖️"),
    (("process","step","workflow"), "🔁"),
    (("tip","note","important","key"), "💡"),
    (("tree","hierarchy","parent","child"), "🌳"),
    (("data","memory","state"), "🧠"),
]

def get_point_icon(theme_key: str, index: int) -> str:
    seq = THEME_BULLETS.get(theme_key, THEME_BULLETS["minimalist"])
    return seq[index % len(seq)]

def get_semantic_icon(text: str, theme_key: str) -> str:
    low = (text or "").lower()
    for keys, icon in SEMANTIC:
        if any(k in low for k in keys):
            return icon
    return get_point_icon(theme_key, 0)
