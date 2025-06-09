# voice_integration.py

from faster_whisper import WhisperModel
from gtts import gTTS
from uuid import uuid4
import tempfile
import os

# Model setup
model = WhisperModel("base", compute_type="int8")  # or "small"

# Audio transcription
def transcribe_audio_django(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    segments, _ = model.transcribe(tmp_path)
    text = " ".join(segment.text for segment in segments)
    return text

# Text-to-speech
OUTPUT_FOLDER = "media/audio"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def synthesize_speech(text: str) -> str:
    filename = f"{uuid4()}.mp3"
    path = os.path.join(OUTPUT_FOLDER, filename)

    tts = gTTS(text=text, lang='fr')
    tts.save(path)

    return f"/media/audio/{filename}"
