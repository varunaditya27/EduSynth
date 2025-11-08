# backend/app/ai_animator.py
"""
ai_animator.py
Generate short Manim animations per slide and return MP4 path.
Designed to integrate with your existing video_sync pipeline.

Requirements:
 - manim (community) installed: pip install manim
 - ffmpeg available on PATH (you already have it)
 - Python >= 3.8

Behavior:
 - For each slide we produce a small Manim Scene file that:
    * Shows the slide title
    * Animates bullet points appearing one-by-one in sync with durations
 - Calls the `manim` CLI (subprocess) to render the clip to MP4
 - Returns the final mp4 path (or raises on failure)
"""

from pathlib import Path
import subprocess
import json
import shlex
import time
import math
import re

# Where manim will place its media (default)
# We'll search in project_media_dir / "media" afterwards to find the mp4
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "output"

def _sanitize_filename(s: str) -> str:
    s = re.sub(r"[^\w\-_\. ]", "_", s)
    s = re.sub(r"\s+", "_", s)
    return s[:120]

def _write_scene_py(out_dir: Path, slide: dict, theme: str):
    """
    Writes a manim python scene file that animates the slide title and bullets.
    out_dir: folder to write scene.py into
    Returns the path to the scene file and the SceneClass name to call.
    """
    idx = int(slide.get("index", 0))
    title = slide.get("title", f"Slide {idx}")
    points = slide.get("points", [])
    narration = slide.get("narration", "")
    duration = float(slide.get("display_duration", slide.get("audio_duration", 5.0)))

    # compute per-step durations (title + per-bullet)
    steps = max(1, len(points))
    # leave some lead/trail time, distribute duration among steps
    total_for_steps = max(0.6 * duration, 0.1 * duration)
    per_step = total_for_steps / max(1, steps)

    # generate safe python identifier name
    scene_name = f"SlideScene_{idx}"
    filename = f"scene_slide_{idx}.py"
    scene_path = out_dir / filename

    # Basic Manim scene code
    # We use simple Text mobjects to keep render time low.
    code = f'''
from manim import *

class {scene_name}(Scene):
    def construct(self):
        config.background_color = WHITE  # will be swapped below if theme is dark
        title = Text("{title}", font_size=48)
        title.to_edge(UP)
        self.play(Write(title), run_time=1)

        bullets = VGroup()
'''
    # add bullet text objects (escape quotes)
    for i, p in enumerate(points):
        text = p.replace('"', "'").replace("\n", " ")
        code += f'        b{i} = Text("{text}", font_size=36)\n'
        code += f'        b{i}.next_to(title, DOWN, buff={1.0 + i*0.6})\n'
        code += f'        bullets.add(b{i})\n'

    code += "\n"
    # sequence animations timed approximately per_step
    for i in range(len(points)):
        rt = max(0.6, per_step)  # small minimum
        code += f'        self.wait(0.2)\n'
        code += f'        self.play(FadeIn(b{i}), run_time={rt})\n'

    # keep final frame visible
    code += f'        self.wait(0.5)\n'

    # theme handling (basic)
    if theme.lower() in ["chalkboard", "neon", "gradient"]:
        # dark backgrounds -> set background and text color to light
        code = code.replace("config.background_color = WHITE", "config.background_color = BLACK")
        # also apply white color to text objects after creation (simple approach)
        # We append after construction: set color of all Text to WHITE
        code += "\n        for mob in self.mobjects:\n            if isinstance(mob, Text):\n                mob.set_color(WHITE)\n"

    # write file
    out_dir.mkdir(parents=True, exist_ok=True)
    scene_path.write_text(code, encoding="utf-8")
    return scene_path, scene_name

def _find_manim_output(scene_file: Path, scene_name: str) -> Path:
    """
    Manim's CLI writes to media/videos/<scene_file_stem>/<scene_name>/<resolution>.mp4
    This function searches for that mp4 and returns it if found.
    """
    media_root = Path.cwd() / "media"
    # manim writes under CWD/media by default. use project root CWD when invoking subprocess.
    # search for relevant files
    stem = scene_file.stem
    candidates = list(media_root.rglob(f"{scene_name}.mp4"))
    if candidates:
        return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    # fallback: search by stem
    candidates2 = list(media_root.rglob(f"{stem}*.mp4"))
    if candidates2:
        return sorted(candidates2, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    raise FileNotFoundError("Rendered manim mp4 not found in media/")

def generate_manim_clip(slide: dict, task_id: str, theme: str = "Minimalist", manim_quality: str = "low"):
    """
    Generate a short manim animation for the slide.
    Returns path to mp4 on success.

    manim_quality: 'low'|'medium'|'high' mapped to manim flags
    """
    task_dir = OUTPUT_ROOT / task_id / "ai_clips"
    task_dir.mkdir(parents=True, exist_ok=True)

    # write scene file
    scene_file, scene_name = _write_scene_py(task_dir, slide, theme)

    # Choose manim rendering quality flags
    quality_map = {
        "low": ["-ql"],      # quick low quality
        "medium": ["-qm"],
        "high": ["-qh"]
    }
    qflags = quality_map.get(manim_quality, ["-ql"])

    # CLI: manim [quality flag] scene_file.py SceneClass
    # We must run from project root so media/ appears in project_root/media
    cmd = ["manim", *qflags, str(scene_file), scene_name]
    try:
        # run manim; ensure we run in the project root
        print(f"[MANIM] Rendering scene: {' '.join(cmd)}")
        proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            # surface stderr for debugging
            raise RuntimeError(f"Manim render failed: {proc.stderr}\nCMD: {' '.join(cmd)}")
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("Manim rendering timed out") from e

    # find the output mp4
    try:
        mp4 = _find_manim_output(scene_file, scene_name)
    except FileNotFoundError:
        # manim sometimes writes to other folders; search by timestamp in media
        media_root = PROJECT_ROOT / "media"
        matches = list(media_root.rglob("*.mp4"))
        if matches:
            mp4 = sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        else:
            raise

    # copy or move the mp4 to task folder with desired name
    dest = task_dir / f"slide_{int(slide.get('index',0))}_manim.mp4"
    mp4.replace(dest)
    print(f"[MANIM] Generated clip saved: {dest}")
    return dest.as_posix()
