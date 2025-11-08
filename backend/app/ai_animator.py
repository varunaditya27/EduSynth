# backend/app/ai_animator.py
"""
ai_animator.py
Generate short Manim animations per slide and return MP4 path.
Designed to integrate with your existing video_sync pipeline.

✅ Fixes:
 - Keeps theme background constant (no forced black/white)
 - Renders with transparency (so can composite over themed slide)
 - Retains original logic for text animations
"""

from pathlib import Path
import subprocess
import re

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

    # Transparent background for compositing
    code = f'''
from manim import *

class {scene_name}(Scene):
    def construct(self):
        # Transparent background compositing
        title = Text("{title}", font_size=48)
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
    media_root = Path.cwd() / "media"
    candidates = list(media_root.rglob(f"{scene_name}.mp4"))
    if candidates:
        return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    raise FileNotFoundError("Rendered manim mp4 not found in media/")


def generate_manim_clip(slide: dict, task_id: str, theme: str = "Minimalist", manim_quality: str = "low"):
    task_dir = OUTPUT_ROOT / task_id / "ai_clips"
    task_dir.mkdir(parents=True, exist_ok=True)
    scene_file, scene_name = _write_scene_py(task_dir, slide, theme)

    quality_map = {"low": ["-ql"], "medium": ["-qm"], "high": ["-qh"]}
    qflags = quality_map.get(manim_quality, ["-ql"])

    cmd = ["manim", *qflags, str(scene_file), scene_name, "--transparent"]
    print(f"[MANIM] Rendering scene: {' '.join(cmd)}")

    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Manim render failed: {proc.stderr}")

    mp4 = _find_manim_output(scene_file, scene_name)
    dest = task_dir / f"slide_{int(slide.get('index', 0))}_manim.mp4"
    mp4.replace(dest)
    print(f"[MANIM] Generated clip saved: {dest}")
    return dest.as_posix()
