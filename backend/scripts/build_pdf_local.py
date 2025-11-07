#!/usr/bin/env python3
"""
Local PDF builder script for testing.
Loads lecture plan from JSON and generates PDF with cheat-sheet + notes.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

from app.schemas.slides import LecturePlan
from app.services.slides.theme_tokens import get_theme
from app.services.slides.pdf_builder import build_pdf


def main():
    """
    CLI entry point for local PDF generation.
    """
    parser = argparse.ArgumentParser(
        description="Generate PDF from lecture plan JSON"
    )
    parser.add_argument(
        "--input",
        "-i",
        default="samples/lecture_plan.json",
        help="Path to lecture plan JSON file"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output PDF path (default: artifacts/{timestamp}/notes.pdf)"
    )
    parser.add_argument(
        "--theme",
        "-t",
        help="Override theme (minimalist, chalkboard, corporate)"
    )
    parser.add_argument(
        "--cheatsheet-only",
        action="store_true",
        help="Only generate cheat-sheet pages (mindmap + flowchart)"
    )
    parser.add_argument(
        "--notes-only",
        action="store_true",
        help="Only generate lecture notes pages"
    )
    
    args = parser.parse_args()
    
    # Load lecture plan
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
        
        # Validate with Pydantic model
        plan = LecturePlan(**plan_data)
        
    except Exception as e:
        print(f"❌ Error loading lecture plan: {e}")
        sys.exit(1)
    
    # Override theme if specified
    if args.theme:
        plan.theme = args.theme
    
    # Get theme tokens
    try:
        theme = get_theme(plan.theme)
    except Exception as e:
        print(f"❌ Error loading theme: {e}")
        sys.exit(1)
    
    # Determine render mode
    cheatsheet_only = args.cheatsheet_only
    notes_only = args.notes_only
    
    if cheatsheet_only and notes_only:
        print("❌ Error: Cannot use both --cheatsheet-only and --notes-only")
        sys.exit(1)
    
    # Generate PDF
    try:
        pdf_bytes = build_pdf(plan, theme, cheatsheet_only=cheatsheet_only, notes_only=notes_only)
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = backend_root / "artifacts" / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "notes.pdf"
    
    # Write PDF
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        
    except Exception as e:
        print(f"❌ Error writing PDF: {e}")
        sys.exit(1)
    
    # Calculate page counts
    if cheatsheet_only:
        total_pages = 2
        page_breakdown = "Pages 1-2: Cheat-sheet (Mindmap + Flowchart)"
    elif notes_only:
        total_pages = len(plan.slides)
        page_breakdown = f"Pages 1-{total_pages}: Lecture notes"
    else:
        total_pages = len(plan.slides) + 2
        page_breakdown = f"Page 1: Mindmap\nPage 2: Flowchart\nPages 3-{total_pages}: Lecture notes"
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 PDF Generation Summary")
    print("=" * 60)
    print(f"Topic:        {plan.topic}")
    print(f"Theme:        {plan.theme}")
    print(f"Slides:       {len(plan.slides)}")
    print(f"Total Pages:  {total_pages}")
    print(f"Output:       {output_path}")
    print(f"Size:         {len(pdf_bytes) / 1024:.1f} KB")
    print("=" * 60)
    print("\nℹ️  PDF Structure:")
    for line in page_breakdown.split('\n'):
        print(f"   • {line}")
    print("\n✨ Done!")


if __name__ == "__main__":
    main()