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
# Fix ImageMagick path for MoviePy TextClip
os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"

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
        # ✅ FIX: Use LANCZOS instead of ANTIALIAS
        img = Image.open(bg_path).convert("RGB").resize(DEFAULT_SIZE, Image.Resampling.LANCZOS)
    return img

# ---------------------------------------------------------
# UTILITY HELPERS
# ---------------------------------------------------------
def _is_dark_image(img: Image.Image) -> bool:
    grayscale = img.convert("L")
    stat = ImageStat.Stat(grayscale)
    return stat.mean[0] < 127


def _draw_fallback_subtitle(base_img: Image.Image, text: str, font_size: int = 24):
    """Fallback subtitle rendering using Pillow (Pillow>=10 safe) - IMPROVED."""
    draw = ImageDraw.Draw(base_img)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # ✅ IMPROVED: Better dimensions and positioning
    box_height = 140
    padding_bottom = 20
    padding_sides = int(base_img.width * 0.05)  # 5% padding on each side
    
    overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    y_start = base_img.height - box_height - padding_bottom
    draw_overlay.rectangle([(0, y_start), (base_img.width, base_img.height)], fill=(0, 0, 0, 153))  # 60% opacity
    base_img = Image.alpha_composite(base_img.convert("RGBA"), overlay)

    # Draw text (using textbbox) with better wrapping
    draw = ImageDraw.Draw(base_img)  # ✅ Redraw after composite
    
    # ✅ Calculate optimal wrap width based on image width and font
    chars_per_line = int((base_img.width - 2 * padding_sides) / (font_size * 0.6))
    lines = textwrap.fill(text, width=chars_per_line).split("\n")
    
    # Center text vertically within the box
    total_text_height = len(lines) * (font_size + 6)
    y_text = y_start + (box_height - total_text_height) // 2
    
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
        # ✅ FIX: MoviePy doesn't have zoom_in in vfx module
        # Use resize with interpolation instead
        w, h = img_clip.size
        final_w = int(w * zoom)
        final_h = int(h * zoom)
        
        def zoom_effect(get_frame, t):
            frame = get_frame(t)
            progress = t / img_clip.duration
            current_zoom = 1 + (zoom - 1) * progress
            new_w = int(w * current_zoom)
            new_h = int(h * current_zoom)
            
            # Resize frame
            from PIL import Image
            pil_img = Image.fromarray(frame)
            resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Center crop to original size
            left = (new_w - w) // 2
            top = (new_h - h) // 2
            cropped = resized.crop((left, top, left + w, top + h))
            
            return np.array(cropped)
        
        from moviepy.video.VideoClip import VideoClip
        return img_clip.fl(lambda gf, t: zoom_effect(gf, t), apply_to=['mask'])
    except Exception as e:
        print(f"[Ken Burns] Failed: {e}")
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
        title = s.get("title", f"Slide {idx}")
        points = s.get("points", [])
        narration = s.get("narration", "")
        duration = float(s.get("display_duration", s.get("audio_duration", 5.0)))
        audio_path = s.get("audio_path")

        print(f"\n[SLIDE {idx}] Processing: '{title}'")
        print(f"  Points: {len(points)} bullets")
        print(f"  Narration: {narration[:60]}...")
        print(f"  Duration: {duration}s")

        # ✅ Create background clip with EXACT duration to match audio
        bg_array = np.array(base_img)
        bg_clip = ImageClip(bg_array).set_duration(duration)
        print(f"  [BACKGROUND] Set to {duration}s to match audio")

        # --- 1️⃣ Try Manim Animation ---
        clip = None
        if use_manim:
            try:
                print(f"  [MANIM] Attempting to render slide {idx}...")
                path = generate_manim_clip(s, task_id, theme)
                
                # ✅ Load MOV file with alpha channel
                manim_video = VideoFileClip(path, has_mask=True)
                manim_duration = manim_video.duration
                
                print(f"  [MANIM] Video duration: {manim_duration:.2f}s, Target: {duration:.2f}s")
                
                # ✅ TIMING SYNC: Handle duration mismatch
                if abs(manim_duration - duration) > 0.5:
                    print(f"  [MANIM] ⚠️ Duration mismatch detected! Adjusting...")
                    if manim_duration > duration:
                        # Manim is longer - trim it
                        manim_clip = manim_video.subclip(0, duration)
                        print(f"  [MANIM] Trimmed to {duration}s")
                    else:
                        # Manim is shorter - slow it down to match
                        speed_factor = manim_duration / duration
                        manim_clip = manim_video.fx(vfx.speedx, speed_factor)
                        print(f"  [MANIM] Slowed down by {speed_factor:.2f}x to match audio")
                else:
                    manim_clip = manim_video
                
                # Ensure exact duration match
                manim_clip = manim_clip.set_duration(duration)
                
                # ✅ CRITICAL: Composite Manim animation OVER themed background
                clip = CompositeVideoClip([bg_clip, manim_clip.set_position("center")])
                print(f"  [MANIM] ✅ Success! Composited over {theme} background (synced: {duration}s)")
            except Exception as e:
                print(f"  [MANIM] ❌ Failed: {e}")
                import traceback
                traceback.print_exc()

        # --- 2️⃣ Static Fallback with Ken Burns ---
        if clip is None:
            print(f"  [FALLBACK] Using static background with Ken Burns effect")
            
            # ✅ CRITICAL FIX: Manually render slide content onto background
            slide_img = base_img.copy()
            draw = ImageDraw.Draw(slide_img)
            
            try:
                title_font = ImageFont.truetype("arial.ttf", 48)
                point_font = ImageFont.truetype("arial.ttf", 32)
            except:
                title_font = ImageFont.load_default()
                point_font = ImageFont.load_default()
            
            # Draw title at top
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_w = title_bbox[2] - title_bbox[0]
            title_x = (slide_img.width - title_w) / 2
            draw.text((title_x, 60), title, font=title_font, fill=text_color)
            
            # Draw bullet points
            y_offset = 180
            for i, point in enumerate(points):
                wrapped_text = textwrap.fill(point, width=60)
                for line in wrapped_text.split('\n'):
                    draw.text((100, y_offset), f"• {line}", font=point_font, fill=text_color)
                    y_offset += 50
            
            slide_array = np.array(slide_img)
            slide_clip = ImageClip(slide_array).set_duration(duration)
            clip = _apply_ken_burns(slide_clip, 1.05)

        # --- 3️⃣ Contextual Tenor Animation (right side) ---
        anim_path = _get_contextual_animation(narration)
        if anim_path:
            try:
                print(f"  [TENOR] Adding contextual animation...")
                tenor_clip = VideoFileClip(anim_path)
                
                # Limit duration to slide or 10 seconds max
                tenor_duration = min(duration, 10, tenor_clip.duration)
                anim_clip = tenor_clip.subclip(0, tenor_duration)
                
                # ✅ Resize using MoviePy's built-in method (no PIL ANTIALIAS issue)
                anim_w = int(clip.w * 0.33)
                anim_clip = anim_clip.resize(width=anim_w)
                
                overlay_x = int(clip.w * 0.60)
                overlay_y = int(clip.h * 0.25)
                anim_clip = anim_clip.set_position((overlay_x, overlay_y)).fadein(0.4).fadeout(0.4)
                clip = CompositeVideoClip([clip, anim_clip])
                print(f"  [TENOR] ✅ Overlay added!")
            except Exception as e:
                print(f"  [TENOR] ❌ Overlay failed: {e}")
                import traceback
                traceback.print_exc()

        # --- 4️⃣ Subtitles (Fixed positioning and sizing) ---
        if narration.strip():
            try:
                print(f"  [SUBTITLE] Rendering subtitles...")
                
                # ✅ FIXED: Better subtitle dimensions and positioning
                subtitle_width = int(clip.w * 0.90)  # 90% of video width (more space)
                subtitle_height = 140  # Slightly shorter to fit better
                subtitle_y_position = clip.h - 160  # More padding from bottom
                
                # Create subtitle text with proper wrapping
                sub = TextClip(
                    narration,
                    fontsize=24,  # Slightly smaller for better fit
                    color=text_color,
                    font="Arial",
                    method="caption",
                    size=(subtitle_width, None),  # Auto-height based on content
                    align="center",
                ).set_position(("center", subtitle_y_position)).set_duration(duration)

                # Background box with proper dimensions
                bg_box = TextClip(
                    " ", 
                    fontsize=24, 
                    size=(clip.w, subtitle_height), 
                    color="black"
                )
                bg_box = bg_box.set_opacity(0.6).set_position(("center", subtitle_y_position - 10)).set_duration(duration)
                
                clip = CompositeVideoClip([clip, bg_box, sub])
                print(f"  [SUBTITLE] ✅ Added! (width: {subtitle_width}px, height: {subtitle_height}px)")
            except Exception as e:
                print(f"  [SUBTITLE] ❌ Failed with TextClip: {e}")
                print(f"  [SUBTITLE] Using Pillow fallback...")
                try:
                    fallback = _draw_fallback_subtitle(base_img.copy(), narration)
                    clip = ImageClip(np.array(fallback)).set_duration(duration)
                    print(f"  [SUBTITLE] ✅ Fallback success!")
                except Exception as e2:
                    print(f"  [SUBTITLE] ❌ Fallback also failed: {e2}")

        # --- 5️⃣ Attach Audio ---
        if audio_path and os.path.exists(audio_path):
            try:
                audio = AudioFileClip(audio_path).set_start(current_time)
                audio_clips.append(audio)
                print(f"  [AUDIO] ✅ Attached: {Path(audio_path).name}")
            except Exception as e:
                print(f"  [AUDIO] ❌ Failed: {e}")

        clip = clip.fadein(0.4).fadeout(0.4)
        video_clips.append(clip)
        current_time += duration

    # --- 6️⃣ Merge Everything ---
    print(f"\n[FINAL] Concatenating {len(video_clips)} clips...")
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
        verbose=True,  # ✅ Changed to True for better debugging
    )

    print(f"✅ Final video saved → {out_path}")
    return out_path.as_posix()
