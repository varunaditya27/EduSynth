# backend/app/ai_animator.py
"""
ai_animator.py
Generate short Manim animations per slide and return MP4 path.
Designed to integrate with your existing video_sync pipeline.

✅ Fixes:
 - Keeps theme background constant (no forced black/white)
 - Renders with transparency (so can composite over themed slide)
 - Retains original logic for text animations
 - FIXED: Manim output location finder for newer Manim versions
"""

from pathlib import Path
import subprocess
import re
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "output"


def _sanitize_filename(s: str) -> str:
    s = re.sub(r"[^\w\-_\. ]", "_", s)
    s = re.sub(r"\s+", "_", s)
    return s[:120]


def _write_scene_py(out_dir: Path, slide: dict, theme: str):
    idx = int(slide.get("index", 0))
    title = slide.get("title", f"Slide {idx}")
    points = slide.get("points", [])
    duration = float(slide.get("display_duration", slide.get("audio_duration", 5.0)))

    steps = max(1, len(points))
    total_for_steps = max(0.6 * duration, 0.1 * duration)
    per_step = total_for_steps / max(1, steps)

    scene_name = f"SlideScene_{idx}"
    filename = f"scene_slide_{idx}.py"
    scene_path = out_dir / filename

    # ✅ CRITICAL: Set camera background to TRANSPARENT for compositing
    code = f'''
from manim import *

config.background_opacity = 0  # ✅ Make background fully transparent

class {scene_name}(Scene):
    def construct(self):
        # Configure transparent background
        self.camera.background_color = "#00000000"  # Transparent black
        
        title = Text("{title}", font_size=48, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title), run_time=1)

        bullets = VGroup()
'''

    for i, p in enumerate(points):
        text = p.replace('"', "'").replace("\n", " ")
        code += f'        b{i} = Text("{text}", font_size=36)\n'
        code += f'        b{i}.next_to(title, DOWN, buff={1.0 + i*0.6})\n'
        code += f'        bullets.add(b{i})\n'

    for i in range(len(points)):
        rt = max(0.6, per_step)
        code += f'        self.wait(0.2)\n'
        code += f'        self.play(FadeIn(b{i}), run_time={rt})\n'

    code += f'        self.wait(0.5)\n'

    # Optional color tweak for dark themes
    if theme.lower() in ["chalkboard", "neon", "gradient"]:
        code += "\n        for mob in self.mobjects:\n            if isinstance(mob, Text):\n                mob.set_color(WHITE)\n"

    out_dir.mkdir(parents=True, exist_ok=True)
    scene_path.write_text(code, encoding="utf-8")
    return scene_path, scene_name


def _find_manim_output(scene_file: Path, scene_name: str) -> Path:
    """
    ✅ FIXED: Manim outputs .mov files with --transparent flag for true alpha channel
    """
    # Wait for file system
    time.sleep(0.5)
    
    media_root = PROJECT_ROOT / "media"
    
    print(f"[MANIM] Searching for {scene_name}.mov (transparent MOV with alpha channel)...")
    
    # ✅ Search for .mov files (Manim's transparent output format with alpha)
    possible_paths = [
        media_root / "videos" / scene_file.stem / "480p15" / f"{scene_name}.mov",
        media_root / "videos" / scene_file.stem / "720p30" / f"{scene_name}.mov",
        media_root / "videos" / scene_file.stem / "1080p60" / f"{scene_name}.mov",
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"[MANIM] ✅ Found output at: {path}")
            return path
    
    # Strategy 2: Recursive search with exact name
    if media_root.exists():
        candidates = list(media_root.rglob(f"{scene_name}.mp4"))
        if candidates:
            latest = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
            print(f"[MANIM] ✅ Found via recursive search: {latest}")
            return latest
    
    # Strategy 3: Search in current working directory
    cwd_media = Path.cwd() / "media"
    if cwd_media.exists():
        candidates = list(cwd_media.rglob(f"{scene_name}.mp4"))
        if candidates:
            latest = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
            print(f"[MANIM] ✅ Found in CWD media: {latest}")
            return latest
    
    # Strategy 4: Last resort - any SlideScene_*.mp4 created recently
    all_media_paths = [media_root, cwd_media, PROJECT_ROOT]
    for base in all_media_paths:
        if not base.exists():
            continue
        candidates = list(base.rglob("SlideScene_*.mp4"))
        if candidates:
            # Filter by creation time (last 30 seconds)
            recent = [p for p in candidates if (time.time() - p.stat().st_mtime) < 30]
            if recent:
                latest = sorted(recent, key=lambda p: p.stat().st_mtime, reverse=True)[0]
                print(f"[MANIM] ✅ Found recent file: {latest}")
                return latest

    # If we still haven't found it, print detailed debug info
    print(f"\n[MANIM] ❌ ERROR: Could not find rendered mp4!")
    print(f"  Scene name: {scene_name}")
    print(f"  Scene file: {scene_file}")
    print(f"  PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"  media_root exists: {media_root.exists()}")
    
    if media_root.exists():
        print(f"\n  Contents of media/:")
        for item in media_root.rglob("*"):
            if item.is_file():
                print(f"    - {item.relative_to(media_root)}")
    
    raise FileNotFoundError(f"[MANIM] Rendered mp4 not found after exhaustive search. Expected: {scene_name}.mp4")


def generate_manim_clip(slide: dict, task_id: str, theme: str = "Minimalist", manim_quality: str = "low"):
    task_dir = OUTPUT_ROOT / task_id / "ai_clips"
    task_dir.mkdir(parents=True, exist_ok=True)
    scene_file, scene_name = _write_scene_py(task_dir, slide, theme)

    quality_map = {"low": ["-ql"], "medium": ["-qm"], "high": ["-qh"]}
    qflags = quality_map.get(manim_quality, ["-ql"])

    # ✅ CRITICAL: Add --transparent and --format=mov for true alpha channel
    cmd = ["manim", *qflags, str(scene_file), scene_name, "--transparent", "--format=mov"]
    print(f"[MANIM] Rendering scene with transparency: {' '.join(cmd)}")
    print(f"[MANIM] Working directory: {PROJECT_ROOT}")

    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    
    # Print Manim output for debugging
    if proc.stdout:
        print(f"[MANIM] STDOUT:\n{proc.stdout}")
    if proc.stderr:
        print(f"[MANIM] STDERR:\n{proc.stderr}")
    
    if proc.returncode != 0:
        raise RuntimeError(f"Manim render failed with code {proc.returncode}: {proc.stderr}")

    mov_file = _find_manim_output(scene_file, scene_name)
    dest = task_dir / f"slide_{int(slide.get('index', 0))}_manim.mov"
    
    # Copy instead of move to preserve original MOV with alpha channel
    import shutil
    shutil.copy2(mov_file, dest)
    
    print(f"[MANIM] ✅ Generated transparent clip saved: {dest}")
    print(f"[MANIM] ℹ️ This MOV file has alpha channel for compositing over themed background")
    return dest.as_posix()