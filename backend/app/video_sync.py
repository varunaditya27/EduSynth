# backend/app/video_sync.py
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageStat
import textwrap
import os
import random
import requests
from dotenv import load_dotenv
import numpy as np

# Load .env for Tenor API key
load_dotenv()
TENOR_API_KEY = os.getenv("TENOR_API_KEY")

# Local Imports
from .ai_animator import generate_manim_clip

# MoviePy Imports
from moviepy.editor import (
    ImageClip,
    VideoFileClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    CompositeAudioClip,
    vfx,
)

# ---------------------------------------------------------
# Global Directories
# ---------------------------------------------------------
OUTDIR = Path(__file__).resolve().parent.parent / "output"
THEMES_DIR = Path(__file__).resolve().parent.parent / "assets" / "themes"
DEFAULT_SIZE = (1280, 720)

# ---------------------------------------------------------
# THEME BACKGROUND HANDLER
# ---------------------------------------------------------
def _get_theme_background(theme: str):
    """Load theme background image; fall back to white background."""
    theme = theme.lower().strip()
    mapping = {
        "chalkboard": "chalkboard.png",
        "minimalist": "minimalist.png",
        "neon": "neon.png",
        "corporate": "corporate.png",
        "paper": "paper.png",
        "gradient": "gradient.png",
    }
    theme_file = mapping.get(theme, "minimalist.png")
    bg_path = THEMES_DIR / theme_file
    if not bg_path.exists():
        print(f"[WARNING] Theme image not found for '{theme}', using white background.")
        img = Image.new("RGB", DEFAULT_SIZE, color=(255, 255, 255))
    else:
        # Use LANCZOS (new Pillow resampling constant)
        img = Image.open(bg_path).convert("RGB").resize(DEFAULT_SIZE, Image.Resampling.LANCZOS)
    return img

# ---------------------------------------------------------
# UTILITY HELPERS
# ---------------------------------------------------------
def _is_dark_image(img: Image.Image) -> bool:
    grayscale = img.convert("L")
    stat = ImageStat.Stat(grayscale)
    return stat.mean[0] < 127


def _draw_fallback_subtitle(base_img: Image.Image, text: str, font_size: int = 28):
    """Fallback subtitle rendering using Pillow (Pillow>=10 safe)."""
    draw = ImageDraw.Draw(base_img)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Background box
    box_height = 160
    overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    y_start = base_img.height - box_height - 60
    draw_overlay.rectangle([(0, y_start), (base_img.width, base_img.height)], fill=(0, 0, 0, 180))
    base_img = Image.alpha_composite(base_img.convert("RGBA"), overlay)

    # Draw text (using textbbox)
    lines = textwrap.fill(text, width=80).split("\n")
    y_text = y_start + 20
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x_text = (base_img.width - w) / 2
        draw.text((x_text, y_text), line, font=font, fill=(255, 255, 255))
        y_text += h + 6
    return base_img.convert("RGB")


def _apply_ken_burns(img_clip, zoom=1.08):
    """Subtle pan/zoom effect to make static slides dynamic."""
    try:
        return img_clip.fx(vfx.zoom_in, final_scale=zoom, duration=img_clip.duration)
    except Exception:
        return img_clip


# ---------------------------------------------------------
# TENOR CONTEXTUAL ANIMATION FETCHER
# ---------------------------------------------------------
def _get_contextual_animation(narration: str):
    """
    Fetch a contextual animation dynamically from Tenor GIF API.
    Returns a downloaded mp4 path if successful.
    """
    if not TENOR_API_KEY or not narration:
        return None

    words = [w.strip(",.!?") for w in narration.lower().split()]
    keywords = [w for w in words if len(w) > 4]
    if not keywords:
        return None

    query = random.choice(keywords[:3])
    url = f"https://tenor.googleapis.com/v2/search?q={query}&key={TENOR_API_KEY}&limit=1"

    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if "results" in data and data["results"]:
            media = data["results"][0]["media_formats"]
            mp4_url = None
            for _, v in media.items():
                if "mp4" in v.get("url", ""):
                    mp4_url = v["url"]
                    break
            if not mp4_url:
                return None

            tmp_dir = OUTDIR / "temp"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = tmp_dir / f"{query}.mp4"

            with requests.get(mp4_url, stream=True, timeout=10) as r:
                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"[GIF API] Downloaded contextual animation for '{query}' → {tmp_path}")
            return tmp_path.as_posix()
    except Exception as e:
        print(f"[GIF API ERROR] {e}")
    return None


# ---------------------------------------------------------
# MAIN VIDEO ASSEMBLY
# ---------------------------------------------------------
def assemble_video_from_slides(task_id: str, slides: list, theme: str = "Minimalist", use_manim: bool = True):
    """
    Builds the full video with:
    - Themed background
    - Manim or Ken Burns slides
    - Tenor contextual animations (right side)
    - Subtitles + TTS audio
    """
    video_dir = OUTDIR / task_id / "video"
    video_dir.mkdir(parents=True, exist_ok=True)

    base_img = _get_theme_background(theme)
    text_color = "white" if _is_dark_image(base_img) else "black"

    video_clips, audio_clips = [], []
    current_time = 0.0

    for s in slides:
        idx = s["index"]
        narration = s.get("narration", "")
        duration = float(s.get("display_duration", s.get("audio_duration", 5.0)))
        audio_path = s.get("audio_path")

        bg_array = np.array(base_img)
        bg_clip = ImageClip(bg_array).set_duration(duration)

        # --- 1️⃣ Try Manim Animation ---
        clip = None
        if use_manim:
            try:
                path = generate_manim_clip(s, task_id, theme)
                manim_clip = VideoFileClip(path).subclip(0, duration)
                clip = CompositeVideoClip([bg_clip, manim_clip])
            except Exception as e:
                print(f"[MANIM] Failed for slide {idx}: {e}")

        # --- 2️⃣ Static Fallback with Ken Burns ---
        if clip is None:
            slide_img = ImageClip(np.array(base_img)).set_duration(duration)
            clip = _apply_ken_burns(slide_img, 1.05)

        # --- 3️⃣ Contextual Tenor Animation (right side) ---
        anim_path = _get_contextual_animation(narration)
        if anim_path:
            try:
                anim_clip = VideoFileClip(anim_path).set_duration(duration)
                anim_clip = anim_clip.resize(width=int(clip.w * 0.33))
                overlay_x = int(clip.w * 0.60)
                overlay_y = int(clip.h * 0.25)
                anim_clip = anim_clip.set_position((overlay_x, overlay_y)).fadein(0.4).fadeout(0.4)
                clip = CompositeVideoClip([clip, anim_clip])
                print(f"[OVERLAY] Added contextual animation for slide {idx}")
            except Exception as e:
                print(f"[OVERLAY] Failed overlay for slide {idx}: {e}")

        # --- 4️⃣ Subtitles ---
        if narration.strip():
            try:
                sub = TextClip(
                    narration,
                    fontsize=28,
                    color=text_color,
                    font="Arial",
                    method="caption",
                    size=(clip.w - 160, 180),
                    align="center",
                ).set_position(("center", clip.h - 120)).set_duration(duration)

                bg_box = TextClip(" ", fontsize=32, size=(clip.w, 180), color="black")
                bg_box = bg_box.set_opacity(0.55).set_position(("center", clip.h - 120)).set_duration(duration)
                clip = CompositeVideoClip([clip, bg_box, sub])
            except Exception as e:
                print(f"[Subtitle Fallback] {e}")
                fallback = _draw_fallback_subtitle(base_img.copy(), narration)
                clip = ImageClip(np.array(fallback)).set_duration(duration)

        # --- 5️⃣ Attach Audio ---
        if audio_path and os.path.exists(audio_path):
            try:
                audio = AudioFileClip(audio_path).set_start(current_time)
                audio_clips.append(audio)
            except Exception as e:
                print(f"Audio attach fail: {e}")

        clip = clip.fadein(0.4).fadeout(0.4)
        video_clips.append(clip)
        current_time += duration

    # --- 6️⃣ Merge Everything ---
    final = concatenate_videoclips(video_clips, method="compose")
    if audio_clips:
        final = final.set_audio(CompositeAudioClip(audio_clips))

    out_path = video_dir / f"{task_id}.mp4"
    print(f"[EXPORT] Rendering final video → {out_path}")

    final.write_videofile(
        out_path.as_posix(),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        audio_bitrate="192k",
        threads=4,
        temp_audiofile=str(video_dir / "temp-audio.m4a"),
        remove_temp=True,
        verbose=False,
    )

    print(f"✅ Final video saved → {out_path}")
    return out_path.as_posix()
