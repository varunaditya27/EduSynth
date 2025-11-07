# backend/app/merge_utils.py
import subprocess
from pathlib import Path

OUTDIR = Path(__file__).resolve().parent.parent / "output"

def merge_audio_video(task_id: str):
    """
    Merges the pre-rendered video and the combined audio tracks into a single MP4.
    """
    video_path = OUTDIR / task_id / "video" / f"{task_id}.mp4"
    audio_dir = OUTDIR / task_id / "audio"
    output_path = OUTDIR / task_id / "final" / f"{task_id}_merged.mp4"

    # Ensure output folder exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Merge all slide audio into one temp audio file
    audio_files = sorted(audio_dir.glob("slide_*.mp3"))
    concat_list = OUTDIR / task_id / "audio_list.txt"

    with concat_list.open("w", encoding="utf-8") as f:
        for af in audio_files:
            f.write(f"file '{af.as_posix()}'\n")

    combined_audio = OUTDIR / task_id / "combined_audio.mp3"

    # Concatenate all mp3s
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list.as_posix(),
        "-c", "copy", combined_audio.as_posix()
    ], check=True)

    # Now merge the combined audio with the video
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path.as_posix(),
        "-i", combined_audio.as_posix(),
        "-c:v", "copy",        # keep video quality
        "-c:a", "aac",         # encode audio
        "-shortest",           # trim to shortest track
        output_path.as_posix()
    ], check=True)

    return output_path.as_posix()
