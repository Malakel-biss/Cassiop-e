from django.urls import path
from .views import lesson_chatbot_view , generate_quiz_view , upload_audio_view, tts_view

urlpatterns = [
    path("lesson/<int:lesson_id>/chat/", lesson_chatbot_view, name="lesson_chatbot"),
    path('lesson/<int:lesson_id>/generate-quiz/', generate_quiz_view, name='generate_quiz'),
    path("upload-audio/", upload_audio_view, name="upload_audio"),
    path("tts/", tts_view, name="tts"),
]
