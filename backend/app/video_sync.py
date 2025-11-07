from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    CompositeAudioClip
)

OUTDIR = Path(__file__).resolve().parent.parent / "output"
THEMES_DIR = Path(__file__).resolve().parent.parent / "assets" / "themes"
DEFAULT_SIZE = (1280, 720)


# ---------------------------------------------------------
# Helper: load theme background
# ---------------------------------------------------------
def _get_theme_background(theme: str):
    """Load theme background image or create default."""
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
def _make_slide_image(task_id: str, slide_index: int, title: str, points: list, theme: str = "Minimalist"):
    """
    Create a slide PNG using theme background and text overlay.
    Uses Pillow to draw title and bullet points.
    """
    slides_dir = OUTDIR / task_id / "slides_images"
    slides_dir.mkdir(parents=True, exist_ok=True)
    w, h = DEFAULT_SIZE

    # Load theme background
    img = _get_theme_background(theme)
    draw = ImageDraw.Draw(img)

    # Dynamic text color based on theme
    dark_themes = ["chalkboard", "neon", "gradient"]
    text_color = (230, 230, 230) if theme.lower() in dark_themes else (20, 20, 20)

    # Fonts: fallback if unavailable
    try:
        font_title = ImageFont.truetype("arial.ttf", 44)
        font_points = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font_title = ImageFont.load_default()
        font_points = ImageFont.load_default()

    # Draw title
    margin = 60
    x, y = margin, margin
    title_wrapped = textwrap.fill(title, width=40)
    draw.text((x, y), title_wrapped, fill=text_color, font=font_title)

    # Draw bullet points
    y += 90
    bullet = "• "
    for p in points:
        p_wrapped = textwrap.fill(p, width=60)
        for line in p_wrapped.splitlines():
            draw.text((x + 10, y), bullet + line, fill=text_color, font=font_points)
            y += 40
            bullet = "  "  # only first line gets bullet
        bullet = "• "

    out_path = slides_dir / f"slide_{slide_index}.png"
    img.save(out_path.as_posix(), format="PNG")
    return out_path.as_posix()


# ---------------------------------------------------------
# Main: assemble video from slides
# ---------------------------------------------------------
def assemble_video_from_slides(task_id: str, slides: list, theme: str = "Minimalist"):
    """
    Assemble video from slides with audio, subtitles, and transitions.
    Creates final MP4 with embedded audio track.
    """
    video_dir = OUTDIR / task_id / "video"
    video_dir.mkdir(parents=True, exist_ok=True)

    # Dynamic color based on theme brightness
    dark_themes = ["chalkboard", "neon", "gradient"]
    text_color = "white" if theme.lower() in dark_themes else "black"

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

        # Create slide image
        img_path = _make_slide_image(task_id, idx, title, points, theme)
        img_clip = ImageClip(img_path).set_duration(duration)

        # Add subtitles with better readability
        if narration.strip():
            try:
                # Create subtitle text
                subtitle_clip = TextClip(
                    narration,
                    fontsize=28,
                    color="white",
                    font="Arial",
                    method="caption",
                    size=(img_clip.w - 200, 140),  # Fixed height for consistency
                    align="center",
                    stroke_color="black",
                    stroke_width=1.5
                ).set_position(("center", img_clip.h - 160)).set_duration(duration)

                # Background semi-transparent box for subtitle
                bg_box = (TextClip(" ", fontsize=32, size=(img_clip.w, 160), color="black")
                          .set_opacity(0.65)
                          .set_position(("center", img_clip.h - 160))
                          .set_duration(duration))

                img_clip = CompositeVideoClip([img_clip, bg_box, subtitle_clip])
            except Exception as e:
                print(f"[WARNING] Could not add subtitle for slide {idx}: {e}")

        # Add fade transitions
        img_clip = img_clip.fadein(0.4).fadeout(0.4)
        video_clips.append(img_clip)

        # Add audio clip with timing
        if audio_path and os.path.exists(audio_path):
            try:
                audio_clip = AudioFileClip(audio_path).set_start(current_time)
                audio_clips_with_timing.append(audio_clip)
                print(f"  ✓ Added audio for slide {idx} at {current_time}s (duration: {duration}s)")
            except Exception as e:
                print(f"  ✗ Failed to load audio for slide {idx}: {e}")
        
        current_time += duration

    # Concatenate all video clips
    print(f"[VIDEO] Concatenating {len(video_clips)} video clips...")
    final_video = concatenate_videoclips(video_clips, method="compose")

    # Merge all audio tracks together
    print("[AUDIO] Compositing audio tracks...")
    if audio_clips_with_timing:
        composite_audio = CompositeAudioClip(audio_clips_with_timing)
        final_video = final_video.set_audio(composite_audio)
        print(f"✓ Audio successfully attached ({len(audio_clips_with_timing)} tracks)")
    else:
        print("[WARNING] No audio tracks found!")

    # Export final video with audio
    out_path = video_dir / f"{task_id}.mp4"
    print(f"[EXPORT] Writing video to {out_path}...")
    
    # CRITICAL: Verify audio is present before export
    if final_video.audio is None:
        print("[ERROR] No audio attached to video!")
    else:
        print(f"[AUDIO] Audio track present: duration={final_video.audio.duration}s")
    
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
        logger="bar"
    )
    
    print(f"✅ Video created successfully: {out_path}")
    print(f"   Duration: {final_video.duration}s")
    print(f"   Audio present: {final_video.audio is not None}")
    
    # Clean up
    for clip in video_clips:
        clip.close()
    for a in audio_clips_with_timing:
        a.close()
    final_video.close()

    return out_path.as_posix()
