# backend/app/tts_utils.py
from elevenlabs import ElevenLabs
from pydub import AudioSegment
from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env file for API key
load_dotenv()

OUTDIR = Path(__file__).resolve().parent.parent / "output"

# Initialize ElevenLabs client
client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

def synthesize_audio(task_id: str, slide_index: int, narration_text: str, voice_name: str = "Rachel"):
    """
    Generate real TTS audio using ElevenLabs API (SDK v2.x).
    Returns (file_path: str, duration_seconds: float)
    """
    task_dir = OUTDIR / task_id / "audio"
    task_dir.mkdir(parents=True, exist_ok=True)

    filename = task_dir / f"slide_{slide_index}.mp3"

    # Default voice: Rachel (you can change it in dashboard)
    voice_id = "EXAVITQu4vr4xnSDxMaL"

    # Generate speech using ElevenLabs streaming API
    response = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        text=narration_text,
        output_format="mp3_44100_128"  # standard quality
    )

    # Write streamed bytes to file
    with open(filename, "wb") as f:
        for chunk in response:
            if isinstance(chunk, bytes):
                f.write(chunk)

    # Measure actual duration using pydub
    audio_seg = AudioSegment.from_file(filename.as_posix())
    duration = round(len(audio_seg) / 1000.0, 3)

    return filename.as_posix(), duration
