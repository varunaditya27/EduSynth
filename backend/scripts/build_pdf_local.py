# backend/scripts/build_pdf_local.py
#!/usr/bin/env python3
"""
EduSynth — Local PDF builder (AESTHETIC MAX + ADAPTIVE)
Generates stunning PDFs for the three themes: minimalist, chalkboard, corporate.
Supports adaptive layouts for desktop/tablet/mobile.

Usage examples:
  python scripts/build_pdf_local.py
  python scripts/build_pdf_local.py --theme corporate
  python scripts/build_pdf_local.py --preset mobile
  python scripts/build_pdf_local.py --orientation portrait
  python scripts/build_pdf_local.py --cheatsheet-only
  python scripts/build_pdf_local.py --notes-only
  python scripts/build_pdf_local.py --input samples/lecture_plan.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Resolve backend root and add to import path so "app.*" imports work
# ──────────────────────────────────────────────────────────────────────────────
THIS_FILE = Path(__file__).resolve()
BACKEND_ROOT = THIS_FILE.parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

# Late imports (after sys.path manipulation)
from app.schemas.slides import LecturePlan  # type: ignore
from app.services.slides.theme_tokens import get_theme  # type: ignore
from app.services.slides.pdf_builder import build_pdf  # type: ignore


# ──────────────────────────────────────────────────────────────────────────────
# Pretty console helpers
# ──────────────────────────────────────────────────────────────────────────────
def print_banner() -> None:
    banner = r"""
╔════════════════════════════════════════════════════════════════════╗
║    ✨ EduSynth PDF Generator — AESTHETIC MAX + ADAPTIVE ✨        ║
╚════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_theme_preview(theme_key: str) -> None:
    info = {
        "minimalist": {
            "icon": "⚪",
            "style": "Ultra-rounded pills, thin elegant lines",
            "colors": "Blue (#2563EB) & Green (#10B981)",
            "personality": "Clean, spacious, modern",
            "features": [
                "Pill-shaped bubbles with colored borders",
                "Subtle shadows for depth",
                "Airy typography",
                "Circular number badges",
                "Generous white space",
            ],
        },
        "chalkboard": {
            "icon": "🎓",
            "style": "Chalk-like lines with soft glow",
            "colors": "Deep green board, Lime (#22C55E) & Chartreuse (#A3E635)",
            "personality": "Educational, warm, engaging",
            "features": [
                "Thick chalk-style strokes",
                "Soft glow accents",
                "High-contrast light text",
                "Playful emoji icons",
                "Subtle board vignette",
            ],
        },
        "corporate": {
            "icon": "💼",
            "style": "Sharp rectangles, professional rhythm",
            "colors": "Blue (#3B82F6) & Cyan (#0EA5E9)",
            "personality": "Formal, structured, authoritative",
            "features": [
                "Header stripes & hairline dividers",
                "Clean shadows and crisp strokes",
                "Labeled bullets & folio",
                "Structured grid & safe bands",
                "Legibility-focused hierarchy",
            ],
        },
    }.get(theme_key.lower(), None)

    key = theme_key.lower()
    if info is None:
        print(f"\nℹ️  Unknown theme '{theme_key}', showing MINIMALIST defaults.")
        return print_theme_preview("minimalist")

    print(f"\n{info['icon']} Theme: {key.upper()}")
    print("─" * 70)
    print(f"Style:       {info['style']}")
    print(f"Colors:      {info['colors']}")
    print(f"Personality: {info['personality']}")
    print("\nKey Features:")
    for feat in info["features"]:
        print(f"  • {feat}")


def format_page_size(width: float, height: float) -> str:
    """Format page dimensions in a human-readable way."""
    # A4 landscape: 841.89 x 595.27
    # A4 portrait: 595.27 x 841.89
    # A5 portrait: 420.94 x 595.27
    
    if abs(width - 841.89) < 1 and abs(height - 595.27) < 1:
        return "A4 Landscape (842×595 pt)"
    elif abs(width - 595.27) < 1 and abs(height - 841.89) < 1:
        return "A4 Portrait (595×842 pt)"
    elif abs(width - 420.94) < 1 and abs(height - 595.27) < 1:
        return "A5 Portrait (421×595 pt)"
    else:
        return f"Custom ({width:.0f}×{height:.0f} pt)"


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate visually distinctive, adaptive PDFs for EduSynth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Notes:
  • --cheatsheet-only renders Mindmap + Flowchart (2 pages)
  • --notes-only renders Lecture Notes only (N pages)
  • Without flags, you get full doc (2 + N pages)
  • --preset overrides --orientation
  • --orientation auto chooses best orientation for content
""",
    )

    parser.add_argument(
        "--input",
        "-i",
        default="samples/lecture_plan.json",
        help="Path to lecture plan JSON (default: samples/lecture_plan.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output PDF path (default: artifacts/TIMESTAMP/<theme>_notes.pdf)",
    )
    parser.add_argument(
        "--theme",
        "-t",
        choices=["minimalist", "chalkboard", "corporate"],
        help="Override theme style (otherwise uses plan.theme)",
    )
    parser.add_argument(
        "--orientation",
        choices=["auto", "portrait", "landscape"],
        help="Page orientation (default: auto)",
    )
    parser.add_argument(
        "--preset",
        choices=["desktop", "tablet", "mobile"],
        help="Device preset (overrides --orientation)",
    )
    parser.add_argument(
        "--cheatsheet-only",
        action="store_true",
        help="Generate only cheat-sheet pages (mindmap + flowchart)",
    )
    parser.add_argument(
        "--notes-only",
        action="store_true",
        help="Generate only lecture notes pages",
    )
    parser.add_argument(
        "--no-ornaments",
        action="store_true",
        help="Disable decorative ornaments on cheat-sheet pages (if any)",
    )
    parser.add_argument(
        "--no-dropcaps",
        action="store_true",
        help="Disable optional drop caps on notes pages (if enabled)",
    )
    parser.add_argument(
        "--preview-theme",
        action="store_true",
        help="Show theme preview and exit (no PDF generation)",
    )

    args = parser.parse_args()

    print_banner()

    # Resolve input path
    input_candidates = [
        Path(args.input),
        BACKEND_ROOT / args.input,
        BACKEND_ROOT / "samples" / "lecture_plan.json",
        BACKEND_ROOT / "app" / "services" / "slides" / "lecture_plan.json",
        BACKEND_ROOT / "lecture_plan.json",
    ]
    input_path: Path | None = next((p for p in input_candidates if p.exists()), None)

    if input_path is None:
        print(f"\n❌ Error: Could not find input file. Tried:")
        for p in input_candidates:
            print(f"   - {p}")
        print("   Please create a lecture_plan.json or pass --input to a valid path.")
        sys.exit(1)

    # Load plan
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
        plan = LecturePlan(**plan_data)
    except Exception as e:
        print(f"\n❌ Error loading lecture plan: {e}")
        sys.exit(1)

    # Apply overrides
    if args.theme:
        plan.theme = args.theme
    if args.preset:
        plan.device_preset = args.preset
    if args.orientation:
        plan.orientation = args.orientation

    # Optional theme preview and exit
    if args.preview_theme:
        print_theme_preview(plan.theme)
        print("\n" + "═" * 70)
        print("Run without --preview-theme to generate the PDF")
        print("═" * 70 + "\n")
        return

    # Load theme tokens
    try:
        theme = get_theme(plan.theme)
        theme["key"] = (plan.theme or "minimalist").lower()
    except Exception as e:
        print(f"\n❌ Error loading theme tokens: {e}")
        sys.exit(1)

    # Validate mode
    cheatsheet_only = bool(args.cheatsheet_only)
    notes_only = bool(args.notes_only)
    if cheatsheet_only and notes_only:
        print("\n❌ Error: Cannot use both --cheatsheet-only and --notes-only")
        sys.exit(1)

    # Calculate expected page size for display
    from reportlab.lib.pagesizes import A4, A5, landscape, portrait
    if plan.device_preset == "desktop":
        page_w, page_h = landscape(A4)
    elif plan.device_preset == "tablet":
        page_w, page_h = portrait(A4)
    elif plan.device_preset == "mobile":
        page_w, page_h = portrait(A5)
    elif plan.orientation == "portrait":
        page_w, page_h = portrait(A4)
    elif plan.orientation == "landscape":
        page_w, page_h = landscape(A4)
    else:  # auto
        page_w, page_h = landscape(A4)  # default assumption
    
    page_size_str = format_page_size(page_w, page_h)

    # Config print
    print("\n📋 Configuration")
    print("─" * 70)
    print(f"Topic:       {plan.topic}")
    print(f"Slides:      {len(plan.slides)}")
    print(f"Duration:    {plan.duration_minutes} minutes")
    print(f"Orientation: {plan.orientation or 'auto'}")
    if plan.device_preset:
        print(f"Preset:      {plan.device_preset}")
    print(f"Page Size:   {page_size_str}")
    
    mode = (
        "Cheat-sheet Only (Title + Flowchart)"
        if cheatsheet_only
        else "Lecture Notes Only"
        if notes_only
        else "Full PDF (Title + Flowchart + Notes)"
    )
    print(f"Mode:        {mode}")

    print_theme_preview(plan.theme)

    # Build PDF
    print("\n🔨 Generating PDF…")
    print("─" * 70)
    try:
        pdf_bytes = build_pdf(
            plan,
            theme,
            cheatsheet_only=cheatsheet_only,
            notes_only=notes_only,
            no_ornaments=args.no_ornaments,
            no_dropcaps=args.no_dropcaps,
        )
        print("✓ PDF rendering complete")
    except Exception as e:
        print(f"\n❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Compute output path
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = (BACKEND_ROOT / output_path).resolve()
        output_dir = output_path.parent
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = (BACKEND_ROOT / "artifacts" / ts).resolve()
    suffix = f"_{plan.device_preset}" if plan.device_preset else f"_{plan.orientation or 'auto'}"
    output_path = output_dir / f"notes{suffix}.pdf"

    # Ensure directory and write
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
    except Exception as e:
        print(f"\n❌ Error writing PDF to {output_path}: {e}")
        sys.exit(1)

    # Stats
    if cheatsheet_only:
        total_pages = 2
    elif notes_only:
        total_pages = len(plan.slides)
    else:
        total_pages = len(plan.slides) + 2

    size_kb = len(pdf_bytes) / 1024
    size_mb = size_kb / 1024
    size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{size_kb:.1f} KB"

    # Summary
    print("\n" + "═" * 70)
    print("✅ SUCCESS! Your adaptive PDF is ready.")
    print("═" * 70)
    print(f"📄 Saved to:   {output_path}")
    print(f"📦 File size:  {size_str}")
    print(f"🧾 Pages:      {total_pages}")
    print(f"📐 Page size:  {page_size_str}")
    if not cheatsheet_only and not notes_only:
        print("\nPage Map:")
        print("  • Page 1:  Title Splash")
        print("  • Page 2:  Process Flowchart (Responsive Grid)")
        if total_pages > 2:
            print(f"  • Pages 3–{total_pages}: Lecture Notes (with pagination)")
    print("\nPro tips:")
    print("  • Try: --theme minimalist | chalkboard | corporate")
    print("  • Try: --preset desktop | tablet | mobile")
    print("  • Try: --orientation auto | portrait | landscape")
    print("  • Iterate fast with: --cheatsheet-only or --notes-only\n")


if __name__ == "__main__":
    main()