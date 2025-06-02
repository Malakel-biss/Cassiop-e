import os
import json
from faster_whisper import WhisperModel
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Load the Whisper model
model = WhisperModel("base", compute_type="int8")

# Define where we store transcripts
TRANSCRIPT_DIR = "media/transcripts"  # Or "data/transcripts"
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

# Function to generate the transcript and save files
def generate_transcript(file_path, lesson_id=None, seconds_per_line=5):
    try:
        print(f"📼 Transcribing video: {file_path}")
        segments, _ = model.transcribe(file_path)
        segments = list(segments)

        # Save the plain transcript (text file)
        plain_lines = [segment.text.strip() for segment in segments if segment.text.strip()]
        text_path = os.path.join(TRANSCRIPT_DIR, f"{lesson_id or 'temp'}_transcript.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write("\n".join(plain_lines))
        print(f"📝 Saved plain transcript to {text_path}")

        # Save the transcript as timed JSON
        json_path = os.path.join(TRANSCRIPT_DIR, f"{lesson_id or 'temp'}_transcript.json")
        result = [{"start": float(segment.start), "end": float(segment.end), "text": segment.text.strip()} for segment in segments]
        with open(json_path, "w", encoding="utf-8") as out:
            json.dump(result, out, indent=2, ensure_ascii=False)
        print(f"✅ Saved timed transcript to {json_path}")

        return "\n".join(plain_lines)

    except Exception as e:
        print("❌ Error during transcription:", e)
        return None
