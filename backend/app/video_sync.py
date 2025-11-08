from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageStat
import textwrap
import os

# Local Imports
from .ai_animator import generate_manim_clip

# --- FORCE IMAGEMAGICK PATH (important for MoviePy TextClip on Windows) ---
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
if os.path.exists(IMAGEMAGICK_PATH):
    os.environ["IMAGEMAGICK_BINARY"] = IMAGEMAGICK_PATH
    print(f"[OK] ImageMagick path set → {IMAGEMAGICK_PATH}")
else:
    print(f"[WARNING] ImageMagick not found at {IMAGEMAGICK_PATH}")

# --- MoviePy Imports ---
from moviepy.editor import (
    ImageClip,
    VideoFileClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    CompositeAudioClip
)

# ---------------------------------------------------------
# Global Directories
# ---------------------------------------------------------
OUTDIR = Path(__file__).resolve().parent.parent / "output"
THEMES_DIR = Path(__file__).resolve().parent.parent / "assets" / "themes"
DEFAULT_SIZE = (1280, 720)

# ---------------------------------------------------------
# Helper: Load Theme Background
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
        img = Image.open(bg_path).convert("RGB").resize(DEFAULT_SIZE)
    return img

# ---------------------------------------------------------
# Helper: Auto-detect brightness for text color switching
# ---------------------------------------------------------
def _is_dark_image(img: Image.Image) -> bool:
    """Return True if image is dark (mean brightness < 127)."""
    grayscale = img.convert("L")
    stat = ImageStat.Stat(grayscale)
    brightness = stat.mean[0]
    return brightness < 127

# ---------------------------------------------------------
# Helper: Create Static Slide Image
# ---------------------------------------------------------
def _make_slide_image(task_id: str, slide_index: int, title: str, points: list, theme: str = "Minimalist"):
    """Create slide PNG with theme background, title, and bullet points."""
    slides_dir = OUTDIR / task_id / "slides_images"
    slides_dir.mkdir(parents=True, exist_ok=True)

    base_img = _get_theme_background(theme)
    draw = ImageDraw.Draw(base_img)
    text_color = (240, 240, 240) if _is_dark_image(base_img) else (25, 25, 25)

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 44)
        font_points = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font_title = ImageFont.load_default()
        font_points = ImageFont.load_default()

    margin = 60
    x, y = margin, margin
    title_wrapped = textwrap.fill(title, width=40)
    draw.text((x, y), title_wrapped, fill=text_color, font=font_title)
    y += 90

    bullet = "• "
    for p in points:
        p_wrapped = textwrap.fill(p, width=60)
        for line in p_wrapped.splitlines():
            draw.text((x + 10, y), bullet + line, fill=text_color, font=font_points)
            y += 40
            bullet = "  "
        bullet = "• "

    out_path = slides_dir / f"slide_{slide_index}.png"
    base_img.save(out_path.as_posix(), format="PNG")
    return out_path.as_posix()

# ---------------------------------------------------------
# Helper: Safe Subtitle Fallback (Pillow-based)
# ---------------------------------------------------------
def _draw_fallback_subtitle(base_img: Image.Image, text: str):
    """If TextClip fails, draw a subtitle directly with Pillow."""
    draw = ImageDraw.Draw(base_img)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()

    # Semi-transparent box
    box_height = 120
    overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    y_start = base_img.height - box_height - 40
    draw_overlay.rectangle(
        [(0, y_start), (base_img.width, base_img.height)],
        fill=(0, 0, 0, 180)
    )
    base_img = Image.alpha_composite(base_img.convert("RGBA"), overlay)

    # Wrap text and draw centered
    lines = textwrap.fill(text, width=80).split("\n")
    y_text = y_start + 30
    for line in lines:
        w, h = draw.textsize(line, font=font)
        x_text = (base_img.width - w) / 2
        draw.text((x_text, y_text), line, font=font, fill=(255, 255, 255))
        y_text += h + 4
    return base_img.convert("RGB")

# ---------------------------------------------------------
# Main: Assemble Final Video
# ---------------------------------------------------------
def assemble_video_from_slides(task_id: str, slides: list, theme: str = "Minimalist", use_manim: bool = True):
    """
    Combines Manim animations (if available) or static slides with narration audio.
    Integrates subtitles, theme-based styling, and fade transitions.
    """
    video_dir = OUTDIR / task_id / "video"
    video_dir.mkdir(parents=True, exist_ok=True)

    base_img = _get_theme_background(theme)
    text_color = "white" if _is_dark_image(base_img) else "black"

    video_clips = []
    audio_clips_with_timing = []
    current_time = 0.0

    for s in slides:
        idx = s["index"]
        title = s.get("title", f"Slide {idx}")
        points = s.get("points", [])
        narration = s.get("narration", "")
        duration = float(s.get("display_duration", s.get("audio_duration", 5.0)))
        audio_path = s.get("audio_path")

        # --- 1️⃣ Try to use Manim animation if enabled ---
        img_clip = None
        if use_manim:
            try:
                ai_clip_path = generate_manim_clip(s, task_id, theme=theme, manim_quality="low")
                img_clip = VideoFileClip(ai_clip_path).subclip(0, duration)
                print(f"[MANIM] Using Manim animation for slide {idx}")
            except Exception as e:
                print(f"[MANIM] Failed for slide {idx}: {e} — falling back to static slide")

        # --- 2️⃣ Fallback to static slide image ---
        if img_clip is None:
            img_path = _make_slide_image(task_id, idx, title, points, theme)
            img_clip = ImageClip(img_path).set_duration(duration)

        # --- 3️⃣ Add subtitles (with Pillow fallback) ---
        if narration.strip():
            try:
                subtitle_clip = TextClip(
                    narration,
                    fontsize=28,
                    color=text_color,
                    font="Arial",
                    method="caption",
                    size=(img_clip.w - 200, 140),
                    align="center",
                    stroke_color="black" if text_color == "white" else "white",
                    stroke_width=1.5
                ).set_position(("center", img_clip.h - 160)).set_duration(duration)

                bg_box = (TextClip(" ", fontsize=32, size=(img_clip.w, 160), color="black")
                          .set_opacity(0.55)
                          .set_position(("center", img_clip.h - 160))
                          .set_duration(duration))

                img_clip = CompositeVideoClip([img_clip, bg_box, subtitle_clip])

            except Exception as e:
                print(f"[WARNING] Subtitle rendering failed on slide {idx}: {e}")
                # Fallback: render subtitle with Pillow and replace image
                print("[FALLBACK] Drawing subtitle with Pillow.")
                fallback_img = _get_theme_background(theme)
                fallback_img = _draw_fallback_subtitle(fallback_img, narration)
                temp_path = OUTDIR / task_id / "slides_images" / f"slide_{idx}_fallback.png"
                fallback_img.save(temp_path)
                img_clip = ImageClip(str(temp_path)).set_duration(duration)

        # --- 4️⃣ Attach audio ---
        if audio_path and os.path.exists(audio_path):
            try:
                audio_clip = AudioFileClip(audio_path).set_start(current_time)
                audio_clips_with_timing.append(audio_clip)
                print(f"  ✓ Audio attached for slide {idx} at {current_time:.2f}s")
            except Exception as e:
                print(f"  ✗ Failed to attach audio for slide {idx}: {e}")

        img_clip = img_clip.fadein(0.4).fadeout(0.4)
        video_clips.append(img_clip)
        current_time += duration

    # --- 5️⃣ Combine all clips ---
    print(f"[VIDEO] Concatenating {len(video_clips)} clips...")
    final_video = concatenate_videoclips(video_clips, method="compose")

    # --- 6️⃣ Merge all audio tracks ---
    print("[AUDIO] Combining audio tracks...")
    if audio_clips_with_timing:
        composite_audio = CompositeAudioClip(audio_clips_with_timing)
        final_video = final_video.set_audio(composite_audio)
    else:
        print("[WARNING] No audio tracks detected!")

    # --- 7️⃣ Export final MP4 ---
    out_path = video_dir / f"{task_id}.mp4"
    print(f"[EXPORT] Rendering final video → {out_path}")

    final_video.write_videofile(
        out_path.as_posix(),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        audio_bitrate="192k",
        threads=4,
        temp_audiofile=str(video_dir / "temp-audio.m4a"),
        remove_temp=True,
        verbose=True,
        logger=None
    )

    print(f"✅ Video created successfully: {out_path}")
    print(f"   Duration: {final_video.duration:.2f}s | Audio attached: {final_video.audio is not None}")

    # --- 8️⃣ Cleanup ---
    for clip in video_clips:
        clip.close()
    for a in audio_clips_with_timing:
        a.close()
    final_video.close()

    return out_path.as_posix()
