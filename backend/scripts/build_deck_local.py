#!/usr/bin/env python3
"""
Local PPTX builder CLI with adaptive layout support.
Generates presentation decks with device presets and orientation options.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import json
from datetime import datetime
from pathlib import Path

from app.schemas.slides import LecturePlan
from app.services.slides.theme_tokens import get_theme
from app.services.slides.pptx_builder import build_pptx
from app.services.slides.thumbnail import render_cover_thumbnail


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_success(msg: str):
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {msg}")


def print_info(msg: str):
    print(f"{Colors.OKCYAN}•{Colors.ENDC} {msg}")


def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{msg}{Colors.ENDC}")


def print_error(msg: str):
    print(f"{Colors.FAIL}✗{Colors.ENDC} {msg}")


def format_size(bytes_val: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def main():
    parser = argparse.ArgumentParser(
        description="Build adaptive PPTX decks locally from LecturePlan JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default settings
  python build_deck_local.py --input samples/lecture_plan.json
  
  # Desktop presentation (16:9 wide)
  python build_deck_local.py -i samples/lecture_plan.json --preset desktop
  
  # Tablet format (4:3 classic)
  python build_deck_local.py -i samples/lecture_plan.json --preset tablet
  
  # Mobile/portrait format (9:16 tall)
  python build_deck_local.py -i samples/lecture_plan.json --preset mobile
  
  # Force landscape orientation
  python build_deck_local.py -i samples/lecture_plan.json --orientation landscape
  
  # Override theme and output location
  python build_deck_local.py -i samples/lecture_plan.json --theme corporate --outdir ~/decks
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        default=str(Path(__file__).resolve().parents[1] / "samples" / "lecture_plan.json"),
        help="Path to LecturePlan JSON (default: backend/samples/lecture_plan.json)",
    )
    
    parser.add_argument(
        "--theme", "-t",
        choices=["minimalist", "chalkboard", "corporate"],
        help="Override theme from JSON (optional)",
    )
    
    parser.add_argument(
        "--preset", "-p",
        choices=["desktop", "tablet", "mobile"],
        help="Device preset: desktop (16:9), tablet (4:3), mobile (9:16)",
    )
    
    parser.add_argument(
        "--orientation", "-r",
        choices=["auto", "portrait", "landscape"],
        help="Force orientation (overrides preset if both specified)",
    )
    
    parser.add_argument(
        "--outdir", "-o",
        default=str(Path(__file__).resolve().parent / "artifacts"),
        help="Output base directory (default: backend/scripts/artifacts)",
    )
    
    parser.add_argument(
        "--no-thumbnail",
        action="store_true",
        help="Skip cover thumbnail generation",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    
    args = parser.parse_args()
    
    # Validate input file
    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print_error(f"Input JSON not found: {in_path}")
        sys.exit(1)
    
    print_header("📊 EduSynth PPTX Builder")
    print_info(f"Input: {in_path.name}")
    
    # Load and validate JSON
    try:
        with open(in_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        
        plan = LecturePlan.model_validate(raw)
        
        if args.verbose:
            print_info(f"Loaded {len(plan.slides)} slides")
    
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        sys.exit(1)
    
    except Exception as e:
        print_error(f"Validation failed: {e}")
        sys.exit(1)
    
    # Apply CLI overrides
    if args.theme:
        plan.theme = args.theme
        if args.verbose:
            print_info(f"Theme override: {args.theme}")
    
    if args.preset:
        plan.device_preset = args.preset
        if args.verbose:
            print_info(f"Device preset: {args.preset}")
    
    if args.orientation:
        plan.orientation = args.orientation
        if args.verbose:
            print_info(f"Orientation: {args.orientation}")
    
    # Get theme configuration
    theme = get_theme(plan.theme)
    
    # Build PPTX
    print_header("🔨 Building Presentation")
    print_info(f"Preset: {plan.device_preset or 'default'}")
    print_info(f"Orientation: {plan.orientation or 'auto'}")
    
    try:
        pptx_bytes = build_pptx(plan, theme)
        print_success(f"PPTX built ({format_size(len(pptx_bytes))})")
    
    except Exception as e:
        print_error(f"PPTX build failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    # Build thumbnail
    thumb_bytes = None
    if not args.no_thumbnail:
        try:
            thumb_bytes = render_cover_thumbnail(plan.topic, theme, size=(1280, 720))
            print_success(f"Thumbnail rendered ({format_size(len(thumb_bytes))})")
        
        except Exception as e:
            print_error(f"Thumbnail generation failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
    
    # Create output directory
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_base = Path(args.outdir).resolve()
    out_dir = out_base / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Write files
    print_header("💾 Saving Files")
    
    deck_path = out_dir / "deck.pptx"
    with open(deck_path, "wb") as f:
        f.write(pptx_bytes)
    print_success(f"PPTX: {deck_path}")
    
    if thumb_bytes:
        cover_path = out_dir / "cover.png"
        with open(cover_path, "wb") as f:
            f.write(thumb_bytes)
        print_success(f"Cover: {cover_path}")
    
    # Summary report
    print_header("📋 Summary")
    print_info(f"Topic:        {plan.topic}")
    print_info(f"Slides:       {len(plan.slides) + 1} (including title)")
    print_info(f"Duration:     {plan.duration_minutes} minutes")
    print_info(f"Language:     {plan.language}")
    
    # Layout details
    preset_info = {
        "desktop": "16:9 wide (13.33\" × 7.5\")",
        "tablet": "4:3 classic (10\" × 7.5\")",
        "mobile": "9:16 portrait (7.5\" × 13.33\")",
    }
    
    preset = plan.device_preset or "desktop"
    print_info(f"Layout:       {preset_info.get(preset, 'custom')}")
    
    print_info(f"Output:       {out_dir}")
    
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Build complete!{Colors.ENDC}\n")
    
    # Open folder on Windows
    try:
        if os.name == "nt":
            os.startfile(str(out_dir))  # type: ignore[attr-defined]
    except Exception:
        pass


if __name__ == "__main__":
    main()