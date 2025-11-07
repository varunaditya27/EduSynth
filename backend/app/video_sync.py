from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, CompositeAudioClip


OUTDIR = Path(__file__).resolve().parent.parent / "output"
THEMES_DIR = Path(__file__).resolve().parent.parent / "assets" / "themes"
DEFAULT_SIZE = (1280, 720)

# ---------------------------------------------------------
# Helper: load theme background
# ---------------------------------------------------------
def _get_theme_background(theme: str):
    theme = theme.lower()
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
        img = Image.new("RGB", DEFAULT_SIZE, color=(255, 255, 255))
    else:
        img = Image.open(bg_path).convert("RGB").resize(DEFAULT_SIZE)
    return img


# ---------------------------------------------------------
# Helper: create slide image
# ---------------------------------------------------------
def assemble_video_from_slides(task_id: str, slides: list, theme: str = "Minimalist"):
    video_dir = OUTDIR / task_id / "final"
    video_dir.mkdir(parents=True, exist_ok=True)

    # Dynamic color based on theme brightness
    dark_themes = ["chalkboard", "neon", "gradient"]
    light_themes = ["minimalist", "corporate", "paper"]
    text_color = "white" if theme.lower() in dark_themes else "black"

    video_clips = []
    audio_clips_with_timing = []
    current_time = 0.0

    for s in slides:
        idx = s["index"]
        title = s.get("title", f"Slide {idx}")
        points = s.get("points", [])
        narration = s.get("narration", "")
        duration = float(s.get("audio_duration", 5.0))
        audio_path = s.get("audio_path")

        img_path = _make_slide_image(task_id, idx, title, points, theme)
        img_clip = ImageClip(img_path).set_duration(duration)

        # Add subtitles
        if narration.strip():
            subtitle_clip = TextClip(
                narration,
                fontsize=30,
                color=text_color,
                font="Arial-Bold",
                method="caption",
                size=(img_clip.w - 200, None),
                align="center",
                stroke_color="black" if text_color == "white" else "white",
                stroke_width=1.5
            ).set_position(("center", img_clip.h - 120)).set_duration(duration)

            # Background semi-transparent box for subtitle
            bg_box = (TextClip(" ", fontsize=32, size=(img_clip.w, 100), color="black")
                      .set_opacity(0.4)
                      .set_position(("center", img_clip.h - 120))
                      .set_duration(duration))

            img_clip = CompositeVideoClip([img_clip, bg_box, subtitle_clip])

        # Add fade transitions
        img_clip = img_clip.fadein(0.4).fadeout(0.4)
        video_clips.append(img_clip)

        # Add audio timing
        if audio_path and os.path.exists(audio_path):
            audio_clip = AudioFileClip(audio_path).set_start(current_time)
            audio_clips_with_timing.append(audio_clip)
        current_time += duration

    # Concatenate all video clips
    final_video = concatenate_videoclips(video_clips, method="compose")

    # Merge all audio tracks together
    if audio_clips_with_timing:
        composite_audio = CompositeAudioClip(audio_clips_with_timing)
        final_video = final_video.set_audio(composite_audio)

    # Export final video
    out_path = video_dir / f"{task_id}_merged.mp4"
    final_video.write_videofile(
        out_path.as_posix(),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        temp_audiofile=str(video_dir / "temp-audio.m4a"),
        remove_temp=True,
        verbose=False,
        logger=None
    )

    print(f"✅ Video created successfully with integrated audio: {out_path}")
    for clip in video_clips:
        clip.close()
    for a in audio_clips_with_timing:
        a.close()
    final_video.close()

    return out_path.as_posix()
