import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

# Import from your slide-deck modules
from app.schemas.slides import LecturePlan
from app.services.slides.theme_tokens import get_theme
from app.services.slides.pptx_builder import build_pptx
from app.services.slides.thumbnail import render_cover_thumbnail


def main():
    parser = argparse.ArgumentParser(
        description="Build a PPTX + cover.png locally from a LecturePlan JSON (no server)."
    )
    parser.add_argument(
        "--input",
        "-i",
        default=str(Path(__file__).resolve().parents[1] / "samples" / "lecture_plan.json"),
        help="Path to LecturePlan JSON (default: backend/samples/lecture_plan.json)",
    )
    parser.add_argument(
        "--theme",
        "-t",
        choices=["minimalist", "chalkboard", "corporate"],
        help="Override theme key (optional).",
    )
    parser.add_argument(
        "--outdir",
        "-o",
        default=str(Path(__file__).resolve().parent / "artifacts"),
        help="Output base directory (default: backend/scripts/artifacts)",
    )
    args = parser.parse_args()

    in_path = Path(args.input).resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input JSON not found: {in_path}")

    with open(in_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Validate via Pydantic model
    plan = LecturePlan.model_validate(raw)

    # Optional theme override
    if args.theme:
        plan.theme = args.theme

    theme = get_theme(plan.theme)

    # Build bytes
    pptx_bytes = build_pptx(plan, theme)
    thumb_bytes = render_cover_thumbnail(plan.topic, theme, size=(1280, 720))

    # Timestamped output folder
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_base = Path(args.outdir).resolve()
    out_dir = out_base / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    deck_path = out_dir / "deck.pptx"
    cover_path = out_dir / "cover.png"

    with open(deck_path, "wb") as f:
        f.write(pptx_bytes)
    with open(cover_path, "wb") as f:
        f.write(thumb_bytes)

    # Little report
    print("✅ Slide deck built successfully")
    print(f"• Topic:        {plan.topic}")
    print(f"• Theme:        {plan.theme}")
    print(f"• Slides:       {len(plan.slides) + 1} (including title)")
    print(f"• PPTX:         {deck_path}")
    print(f"• Cover:        {cover_path}")

    # Helpful hint for Windows: open folder after build
    try:
        if os.name == "nt":
            os.startfile(str(out_dir))  # type: ignore[attr-defined]
    except Exception:
        pass


if __name__ == "__main__":
    main()
