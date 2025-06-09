from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .chatbot_engine import answer_for_lesson
import traceback
from .quiz_generator import generate_quiz_from_lesson
from main_app.models import Lesson
from django.shortcuts import render
from django.http import JsonResponse
from .voice_integration import transcribe_audio_django, synthesize_speech

def upload_audio_view(request):
    if request.method == "POST" and request.FILES.get("audio"):
        try:
            audio_file = request.FILES["audio"]
            text = transcribe_audio_django(audio_file)
            return JsonResponse({"transcription": text})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return render(request, "upload_audio.html")

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def tts_view(request):
    text = request.POST.get("text")
    if not text:
        return JsonResponse({"error": "Missing text"}, status=400)

    try:
        audio_url = synthesize_speech(text)
        return JsonResponse({"audio_url": audio_url})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def upload_and_transcribe(request):
    if request.method == "POST" and request.FILES.get("audio"):
        audio_file = request.FILES["audio"]
        text = transcribe_audio_django(audio_file)
        return JsonResponse({"transcript": text})
    return JsonResponse({"error": "Audio file missing"}, status=400)


from .voice_integration import transcribe_audio_django  # 👈 Add this import

@csrf_exempt
def lesson_chatbot_view(request, lesson_id):
    try:
        print("📥 POST data:", request.POST)
        print("📥 FILES:", request.FILES)

        # Either text input or voice
        if "audio" in request.FILES:
            question = transcribe_audio_django(request.FILES["audio"])
            print("🎙️ Transcribed question:", question)
        else:
            question = request.POST.get("question")
            print("⌨️ Text question:", question)

        if not question:
            return JsonResponse({"error": "Missing question"}, status=400)

        answer = answer_for_lesson(question, lesson_id)
        print("🤖 AI Answer:", answer)

        audio_url = synthesize_speech(answer)
        print("🔊 Audio URL:", audio_url)

        return JsonResponse({"answer": answer, "audio_url": audio_url})

    except Exception as e:
        print("🔥 ERROR in chatbot view:")
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def generate_quiz_view(request, lesson_id):
    if request.method == "POST":
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            quiz_json = generate_quiz_from_lesson(lesson)
            return JsonResponse({"quiz": quiz_json})
        except Lesson.DoesNotExist:
            return JsonResponse({"error": "Lesson not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid method"}, status=405)
