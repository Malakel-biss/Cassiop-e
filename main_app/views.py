import json
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt

from .EmailBackend import EmailBackend
from .models import Attendance, Session, Subject, Course, Lesson, ChatMessage

# Create your views here.


def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    return render(request, 'main_app/login.html')


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Accès refusé</h4>")
    else:
        #Authenticate
        user = EmailBackend.authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user != None:
            login(request, user)
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("staff_home"))
            else:
                return redirect(reverse("student_home"))
        else:
            messages.error(request, "Identifiants invalides")
            return redirect("/")



def logout_user(request):
    if request.user != None:
        logout(request)
    return redirect("/")


@csrf_exempt
def get_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = Attendance.objects.filter(subject=subject, session=session)
        attendance_list = []
        for attd in attendance:
            data = {
                    "id": attd.id,
                    "attendance_date": str(attd.date),
                    "session": attd.session.id
                    }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception as e:
        return None


def showFirebaseJS(request):
    data = """
    // Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in
// your app's Firebase config object.
// https://firebase.google.com/docs/web/setup#config-object
firebase.initializeApp({
    apiKey: "AIzaSyBarDWWHTfTMSrtc5Lj3Cdw5dEvjAkFwtM",
    authDomain: "sms-with-django.firebaseapp.com",
    databaseURL: "https://sms-with-django.firebaseio.com",
    projectId: "sms-with-django",
    storageBucket: "sms-with-django.appspot.com",
    messagingSenderId: "945324593139",
    appId: "1:945324593139:web:03fa99a8854bbd38420c86",
    measurementId: "G-2F2RXTL9GT"
});

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();
messaging.setBackgroundMessageHandler(function (payload) {
    const notification = JSON.parse(payload);
    const notificationOption = {
        body: notification.body,
        icon: notification.icon
    }
    return self.registration.showNotification(payload.notification.title, notificationOption);
});
    """
    return HttpResponse(data, content_type='application/javascript')

def student_panneau(request):
    return render(request, 'main_app/panneau.html')

def courses_view(request):
    courses = Course.objects.all()
    context = {
        'courses': courses
    }
    return render(request, 'main_app/courses.html', context)

def lessons_list_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all().order_by('order')
    context = {
        'course': course,
        'lessons': lessons
    }
    return render(request, 'main_app/lessons_list.html', context)

def lesson_detail_view(request, course_id, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course_id=course_id)
    context = {
        'lesson': lesson
    }
    return render(request, 'main_app/lesson_detail.html', context)

@csrf_exempt
def chat_message(request, lesson_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message')
            lesson = get_object_or_404(Lesson, id=lesson_id)
            
            # Save user message
            ChatMessage.objects.create(
                lesson=lesson,
                user=request.user,
                message=message,
                is_bot=False
            )
            
            # Generate bot response (you can integrate with any AI service here)
            bot_response = generate_bot_response(message, lesson)
            
            # Save bot response
            ChatMessage.objects.create(
                lesson=lesson,
                user=request.user,
                message=bot_response,
                is_bot=True
            )
            
            return JsonResponse({'response': bot_response})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def generate_bot_response(message, lesson):
    """
    Generate a response for the chatbot.
    This is a simple implementation - you can replace it with an AI service.
    """
    # Simple keyword-based responses
    message = message.lower()
    
    if 'help' in message or 'aide' in message:
        return "Je suis là pour vous aider ! Posez-moi des questions sur cette leçon."
    
    if 'pdf' in message or 'document' in message:
        if lesson.pdf:
            return "Vous pouvez trouver le document PDF ci-dessus. Il contient des informations détaillées sur cette leçon."
        return "Désolé, il n'y a pas de document PDF disponible pour cette leçon."
    
    if 'video' in message or 'vidéo' in message:
        if lesson.video:
            return "La vidéo de la leçon est disponible ci-dessus. Vous pouvez la regarder pour une meilleure compréhension."
        return "Désolé, il n'y a pas de vidéo disponible pour cette leçon."
    
    if 'summary' in message or 'résumé' in message:
        return f"Voici un résumé de la leçon '{lesson.title}': {lesson.description[:200]}..."
    
    # Default response
    return "Je suis votre assistant virtuel. Je peux vous aider à comprendre cette leçon. Posez-moi des questions spécifiques sur le contenu."

def add_lesson(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        video = request.FILES.get('video')
        pdf = request.FILES.get('pdf')
        order = request.POST.get('order', 0)
        
        try:
            lesson = Lesson.objects.create(
                course=course,
                title=title,
                description=description,
                video=video,
                pdf=pdf,
                order=order
            )
            messages.success(request, "Lesson added successfully!")
            return redirect('lessons_list', course_id=course.id)
        except Exception as e:
            messages.error(request, f"Could not add lesson: {str(e)}")
    
    context = {
        'course': course,
        'page_title': f'Add Lesson to {course.name}'
    }
    return render(request, 'main_app/add_lesson.html', context)
