import re
import json
from openai import OpenAI
from .memory import get_memory

# ✅ Create OpenAI client for Together.ai
client = OpenAI(
    api_key="188d6df2c6c200770a9497c14c5b9ad37abe4ee69d0f97f16b6d73ef7c89b7f3",
    base_url="https://api.together.xyz/v1"
)

def clean_response(text):
    # Remove <think> tags
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Fix nested "quiz.quiz" structure if present
    try:
        parsed = json.loads(cleaned)
        if "quiz" in parsed and isinstance(parsed["quiz"], dict) and "quiz" in parsed["quiz"]:
            parsed["quiz"] = parsed["quiz"]["quiz"]  # Flatten structure
        return json.dumps(parsed)
    except Exception as e:
        print("⚠️ Could not fully parse and fix quiz JSON:", e)
        return cleaned  # fallback to raw string

def generate_local_answer(prompt, tag=""):
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",  # ✅ WORKING model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
        )
        return clean_response(response.choices[0].message.content.strip())
    except Exception as e:
        print("❌ Error during LLM call:", e)
        raise

def build_quiz_prompt(transcript_text, chat_memory):
    chat_summary = "\n".join(
        f"User: {m['user']}\nBot: {m['bot']}" for m in chat_memory
    )

    return f"""
You are an AI that generates educational multiple-choice quizzes based on a lesson transcript and student conversation.

Generate exactly 5 multiple-choice questions in this strict JSON format:

{{
  "quiz": {{
    "questions": [
      {{
        "question": "What is ...?",
        "options": ["A", "B", "C", "D"],
        "answer": "Correct option here (must match one of the options exactly)"
      }}
    ]
  }}
}}

⚠️ Important:
- Only return the JSON — no explanations, no markdown, no additional text.
- Use exactly ONE "quiz" key — do NOT nest a "quiz" object inside another "quiz" key.

### Transcript:
{transcript_text}

### Conversation:
{chat_summary}
"""

def generate_quiz_from_lesson(lesson):
    full_transcript = lesson.transcript or ""
    memory = get_memory(str(lesson.id)) or []
    transcript_text = full_transcript[:1400]

    prompt = build_quiz_prompt(transcript_text, memory)
    raw_response = generate_local_answer(prompt, tag="quiz")

    try:
        cleaned = re.sub(r"^```json|```$", "", raw_response.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)
    except Exception as e:
        print("❌ Failed to parse quiz JSON:", e)
        print("🔎 Raw response was:", raw_response)
        return {"quiz": {"questions": []}}
