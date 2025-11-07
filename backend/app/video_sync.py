# backend/app/video_sync.py
from pathlib import Path
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import textwrap

OUTDIR = Path(__file__).resolve().parent.parent / "output"

def _make_slide_image(task_id: str, slide_index: int, title: str, points: list, theme: str="Minimalist"):
    """
    Create a placeholder PNG for the slide and return its path.
    Uses Pillow to draw text.
    """
    slides_dir = OUTDIR / task_id / "slides_images"
    slides_dir.mkdir(parents=True, exist_ok=True)
    w, h = 1280, 720

    # Background by theme (simple)
    bg_color = (255, 255, 255)
    text_color = (20, 20, 20)
    if theme.lower().startswith("chalk"):
        bg_color = (30, 30, 30)
        text_color = (230, 230, 230)
    elif theme.lower().startswith("corporate"):
        bg_color = (245, 247, 250)
        text_color = (20, 30, 40)

    img = Image.new("RGB", (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts: fallback to default if not present
    try:
        font_title = ImageFont.truetype("arial.ttf", 44)
        font_points = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font_title = ImageFont.load_default()
        font_points = ImageFont.load_default()

    # Draw title
    margin = 60
    x = margin
    y = margin
    title_wrapped = textwrap.fill(title, width=40)
    draw.text((x, y), title_wrapped, fill=text_color, font=font_title)

    # Draw points
    y += 90
    bullet = "• "
    for p in points:
        p_wrapped = textwrap.fill(p, width=60)
        for line in p_wrapped.splitlines():
            draw.text((x+10, y), bullet + line, fill=text_color, font=font_points)
            y += 40
            bullet = "  "  # only first line gets bullet
        bullet = "• "

    out_path = slides_dir / f"slide_{slide_index}.png"
    img.save(out_path.as_posix(), format="PNG")
    return out_path.as_posix()

def assemble_video_from_slides(task_id: str, slides: list, theme: str="Minimalist"):
    """
    slides: list of dicts with keys: index, title, points, audio_path, audio_duration
    Produces output/video/<task_id>.mp4 and returns the path.
    """
    video_dir = OUTDIR / task_id / "video"
    video_dir.mkdir(parents=True, exist_ok=True)
    clips = []

    for s in slides:
        idx = s["index"]
        title = s.get("title", f"Slide {idx}")
        points = s.get("points", [])
        audio_path = s.get("audio_path")
        audio_duration = float(s.get("audio_duration", 5.0))

        img_path = _make_slide_image(task_id, idx, title, points, theme=theme)

        # Create image clip with duration equal to audio duration
        img_clip = ImageClip(img_path).set_duration(audio_duration)
        if audio_path:
            audio_clip = AudioFileClip(audio_path)
            # ensure durations are in sync
            img_clip = img_clip.set_audio(audio_clip)
        clips.append(img_clip)

    final = concatenate_videoclips(clips, method="compose")
    out_path = video_dir / f"{task_id}.mp4"
    # write the file
    final.write_videofile(out_path.as_posix(), fps=24, audio_codec="aac", threads=0, verbose=False, logger=None)
    return out_path.as_posix()
