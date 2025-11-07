# backend/app/video_sync.py
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


# ---------------------------------------------------------
# Helper: create slide image
# ---------------------------------------------------------
def _make_slide_image(task_id: str, slide_index: int, title: str, points: list, theme: str = "Minimalist"):
    """
    Create a placeholder PNG for the slide and return its path.
    Uses Pillow to draw title and points text.
    """
    slides_dir = OUTDIR / task_id / "slides_images"
    slides_dir.mkdir(parents=True, exist_ok=True)
    w, h = 1280, 720

    # Background + text color by theme
    bg_color = (255, 255, 255)
    text_color = (20, 20, 20)
    if theme.lower().startswith("chalk"):
        bg_color = (30, 30, 30)
        text_color = (230, 230, 230)
    elif theme.lower().startswith("corporate"):
        bg_color = (245, 247, 250)
        text_color = (20, 30, 40)

    # Create blank image
    img = Image.new("RGB", (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)

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
    slides: list of dicts with keys: index, title, points, audio_path, audio_duration, display_duration
    Produces output/video/<task_id>.mp4 and returns the path.
    """
    video_dir = OUTDIR / task_id / "video"
    video_dir.mkdir(parents=True, exist_ok=True)
    
    video_clips = []
    current_time = 0
    
    for s in slides:
        idx = s["index"]
        title = s.get("title", f"Slide {idx}")
        points = s.get("points", [])
        audio_path = s.get("audio_path")
        duration = float(s.get("display_duration", s.get("audio_duration", 5.0)))
        narration = s.get("narration", "")

        # Create image
        img_path = _make_slide_image(task_id, idx, title, points, theme=theme)
        img_clip = ImageClip(img_path).set_duration(duration)

        # Subtitle text (optional)
        if narration.strip():
            try:
                subtitle_clip = TextClip(
                    narration,
                    fontsize=36,
                    color="black",
                    font="Arial-Bold",
                    method="caption",
                    size=(img_clip.w - 100, None),
                    align="center"
                ).set_position(("center", img_clip.h - 150)).set_duration(duration)
                img_clip = CompositeVideoClip([img_clip, subtitle_clip])
            except Exception as e:
                print(f"[WARNING] Could not add subtitle for slide {idx}: {e}")

        # Add fade transitions
        img_clip = img_clip.fadein(0.5).fadeout(0.5)
        video_clips.append(img_clip)
        current_time += duration

    # Concatenate all video clips into one
    print(f"[VIDEO] Concatenating {len(video_clips)} video clips...")
    final_video = concatenate_videoclips(video_clips, method="compose")

    # NOW ADD AUDIO: Load all audio files and composite them at their correct times
    print("[AUDIO] Loading and compositing audio tracks...")
    audio_clips_with_timing = []
    current_time = 0
    
    for s in slides:
        audio_path = s.get("audio_path")
        duration = float(s.get("display_duration", s.get("audio_duration", 5.0)))
        
        if audio_path and os.path.exists(audio_path):
            try:
                audio_clip = AudioFileClip(audio_path)
                # Set the start time for this audio clip
                audio_clip = audio_clip.set_start(current_time)
                audio_clips_with_timing.append(audio_clip)
                print(f"  ✓ Added audio for slide {s['index']} at {current_time}s (duration: {duration}s)")
            except Exception as e:
                print(f"  ✗ Failed to load audio for slide {s['index']}: {e}")
        
        current_time += duration

    # Composite all audio clips together
    if audio_clips_with_timing:
        print(f"[AUDIO] Merging {len(audio_clips_with_timing)} audio tracks...")
        composite_audio = CompositeAudioClip(audio_clips_with_timing)
        final_video = final_video.set_audio(composite_audio)
        print("✓ Audio successfully attached to video")
    else:
        print("[WARNING] No audio tracks found!")

    # Export final video with audio
    out_path = video_dir / f"{task_id}.mp4"
    print(f"[EXPORT] Writing video to {out_path}...")
    
    final_video.write_videofile(
        out_path.as_posix(),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(video_dir / "temp-audio.m4a"),
        remove_temp=True,
        threads=4,
        verbose=False,
        logger=None
    )
    
    print(f"✅ Video created successfully with audio: {out_path}")
    print(f"   Duration: {final_video.duration}s")
    print(f"   Audio present: {final_video.audio is not None}")
    
    # Clean up
    for clip in video_clips:
        clip.close()
    for audio_clip in audio_clips_with_timing:
        audio_clip.close()
    final_video.close()
    
    return out_path.as_posix()