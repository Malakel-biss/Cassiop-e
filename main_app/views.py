import json
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import psutil
import random
from datetime import datetime, timedelta
import time
from django.db.models import Avg, Max, Min, Count
from django.db.models.functions import Trunc

from .EmailBackend import EmailBackend
<<<<<<< HEAD
from .models import Attendance, Session, Subject, Course, Lesson, ChatMessage
=======
from .models import Attendance, Session, Subject, IoTDevice, IoTData, IoTAnalysis, Staff, Student
>>>>>>> develop

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

<<<<<<< HEAD
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
=======
@login_required
def staff_iot_devices(request):
    """Vue pour lister et gérer les appareils IoT"""
    staff = get_object_or_404(Staff, admin=request.user)
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            name = request.POST.get('name')
            device_type = request.POST.get('device_type')
            subject_id = request.POST.get('subject')
            location = request.POST.get('location', '')
            description = request.POST.get('description', '')
            
            # Valider les données
            if not all([name, device_type, subject_id]):
                return JsonResponse({'status': 'error', 'message': 'Tous les champs obligatoires doivent être remplis'})
            
            # Récupérer la matière
            subject = get_object_or_404(Subject, id=subject_id, staff=staff)
            
            # Générer un ID unique pour l'appareil
            device_id = f'DEVICE_{int(time.time())}'
            
            # Créer l'appareil
            device = IoTDevice.objects.create(
                name=name,
                device_id=device_id,
                device_type=device_type,
                description=description,
                location=location,
                subject=subject,
                created_by=staff,
                status='active',
                learning_objective="Analyse des données en temps réel pour comprendre les concepts fondamentaux",
                expected_outcomes="Compréhension des patterns de données et capacité à interpréter les résultats",
                difficulty_level='intermediate'
            )
            
            return JsonResponse({'status': 'success', 'device_id': device.id})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    # GET request - afficher la liste des appareils
    devices = IoTDevice.objects.filter(created_by=staff).select_related('subject')
    
    context = {
        'page_title': 'Gestion des appareils IoT',
        'devices': devices,
        'subjects': Subject.objects.filter(staff=staff),
    }
    return render(request, 'staff_template/staff_iot_devices.html', context)

@login_required
def staff_iot_device_detail(request, device_id):
    """Vue pour afficher les détails d'un appareil IoT et ses données"""
    staff = get_object_or_404(Staff, admin=request.user)
    device = get_object_or_404(IoTDevice, id=device_id, created_by=staff)
    
    # Récupérer les dernières données
    latest_data = IoTData.objects.filter(device=device).order_by('-timestamp')[:100]
    
    # Calculer quelques statistiques de base
    stats = IoTData.objects.filter(device=device).aggregate(
        avg_value=Avg('value'),
        max_value=Max('value'),
        min_value=Min('value'),
        count=Count('id')
    )
    
    # Récupérer les analyses existantes
    analyses = IoTAnalysis.objects.filter(device=device).order_by('-created_at')
    
    context = {
        'page_title': f'Détails de {device.name}',
        'device': device,
        'latest_data': latest_data,
        'stats': stats,
        'analyses': analyses,
    }
    return render(request, 'staff_template/staff_iot_device_detail.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def api_iot_data(request):
    """API endpoint pour recevoir les données des appareils IoT"""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        value = data.get('value')
        unit = data.get('unit', '')
        metadata = data.get('metadata', {})
        
        if not device_id or value is None:
            return JsonResponse({'error': 'Données manquantes'}, status=400)
        
        device = get_object_or_404(IoTDevice, device_id=device_id)
        
        # Créer la nouvelle donnée
        iot_data = IoTData.objects.create(
            device=device,
            value=value,
            unit=unit,
            metadata=metadata
        )
        
        # Mettre à jour la dernière date de réception
        device.last_data_received = timezone.now()
        device.save()
        
        return JsonResponse({
            'status': 'success',
            'data_id': iot_data.id,
            'timestamp': iot_data.timestamp.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def staff_iot_analysis(request, device_id):
    """Vue pour créer et afficher des analyses sur les données IoT"""
    staff = get_object_or_404(Staff, admin=request.user)
    device = get_object_or_404(IoTDevice, id=device_id, created_by=staff)
    
    if request.method == 'POST':
        analysis_type = request.POST.get('analysis_type')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        
        # Récupérer les données pour l'analyse
        data = IoTData.objects.filter(device=device).order_by('timestamp')
        df = pd.DataFrame(list(data.values('timestamp', 'value')))
        
        results = {}
        if analysis_type == 'statistical':
            # Analyse statistique simple
            results = {
                'mean': df['value'].mean(),
                'std': df['value'].std(),
                'min': df['value'].min(),
                'max': df['value'].max(),
                'count': len(df)
            }
        elif analysis_type == 'anomaly':
            # Détection d'anomalies avec Isolation Forest
            scaler = StandardScaler()
            X = scaler.fit_transform(df[['value']])
            clf = IsolationForest(contamination=0.1, random_state=42)
            df['anomaly'] = clf.fit_predict(X)
            results = {
                'anomalies_count': (df['anomaly'] == -1).sum(),
                'normal_count': (df['anomaly'] == 1).sum(),
                'anomaly_percentage': ((df['anomaly'] == -1).sum() / len(df)) * 100
            }
        
        # Créer l'analyse
        analysis = IoTAnalysis.objects.create(
            device=device,
            analysis_type=analysis_type,
            title=title,
            description=description,
            parameters={'type': analysis_type},
            results=results,
            created_by=staff
        )
        
        return JsonResponse({
            'status': 'success',
            'analysis_id': analysis.id,
            'results': results
        })
    
    context = {
        'page_title': f'Analyses - {device.name}',
        'device': device,
        'analyses': IoTAnalysis.objects.filter(device=device).order_by('-created_at')
    }
    return render(request, 'staff_template/staff_iot_analysis.html', context)

@login_required
def student_iot_devices(request):
    """Vue pour les étudiants pour voir les appareils IoT de leurs cours"""
    student = get_object_or_404(Student, admin=request.user)
    devices = IoTDevice.objects.filter(subject__course=student.course)
    
    context = {
        'page_title': 'Appareils IoT',
        'devices': devices,
    }
    return render(request, 'student_template/student_iot_devices.html', context)

@login_required
def student_iot_device_detail(request, device_id):
    """Vue pour les étudiants pour voir les détails d'un appareil IoT"""
    student = get_object_or_404(Student, admin=request.user)
    device = get_object_or_404(IoTDevice, id=device_id, subject__course=student.course)
    
    # Récupérer les dernières données
    latest_data = IoTData.objects.filter(device=device).order_by('-timestamp')[:100]
    
    # Calculer quelques statistiques de base
    stats = IoTData.objects.filter(device=device).aggregate(
        avg_value=Avg('value'),
        max_value=Max('value'),
        min_value=Min('value'),
        count=Count('id')
    )
    
    # Récupérer les analyses publiques
    analyses = IoTAnalysis.objects.filter(device=device).order_by('-created_at')
    
    context = {
        'page_title': f'Détails de {device.name}',
        'device': device,
        'latest_data': latest_data,
        'stats': stats,
        'analyses': analyses,
    }
    return render(request, 'student_template/student_iot_device_detail.html', context)

@login_required
def simulate_cpu_temperature(request):
    """Simule un capteur de température CPU et ajoute des données, en s'assurant qu'il est visible pour les étudiants."""
    staff = get_object_or_404(Staff, admin=request.user)

    # Prendre le premier étudiant existant
    student = Student.objects.first()
    if not student:
        messages.error(request, "Aucun étudiant trouvé dans la base de données.")
        return redirect('staff_iot_devices')

    # Prendre la première matière du cours de l'étudiant
    subject = Subject.objects.filter(course=student.course).first()
    if not subject:
        messages.error(request, "Aucune matière trouvée pour le cours de l'étudiant.")
        return redirect('staff_iot_devices')

    # Créer ou récupérer l'appareil de température CPU
    device, created = IoTDevice.objects.get_or_create(
        device_id='CPU_TEMP_SENSOR',
        defaults={
            'name': 'Capteur de température CPU',
            'device_type': 'temperature',
            'description': 'Capteur simulé de température du CPU',
            'subject': subject,
            'created_by': staff,
            'status': 'active'
        }
    )
    # Si l'appareil existe déjà mais n'est pas lié à la bonne matière, on le met à jour
    if device.subject != subject:
        device.subject = subject
        device.save()

    # Simuler la température CPU (entre 40 et 80 degrés)
    cpu_temp = random.uniform(40, 80)

    # Ajouter la donnée
    IoTData.objects.create(
        device=device,
        value=cpu_temp,
        unit='°C',
        metadata={'cpu_percent': psutil.cpu_percent()}
    )

    # Mettre à jour last_data_received
    device.last_data_received = timezone.now()
    device.save()

    messages.success(request, f'Donnée de température ajoutée : {cpu_temp:.1f}°C')
    return redirect('staff_iot_device_detail', device_id=device.id)

@login_required
def simulate_system_sensor(request):
    """Simule différents types de capteurs système (CPU, mémoire, disque, réseau)"""
    staff = get_object_or_404(Staff, admin=request.user)
    sensor_type = request.GET.get('type', 'cpu')
    
    # Vérifier qu'il existe au moins un étudiant et une matière
    student = Student.objects.first()
    if not student:
        messages.error(request, "Aucun étudiant trouvé dans la base de données.")
        return redirect('staff_iot_devices')
    
    subject = Subject.objects.filter(course=student.course).first()
    if not subject:
        messages.error(request, "Aucune matière trouvée pour le cours de l'étudiant.")
        return redirect('staff_iot_devices')
    
    # Configuration des capteurs selon le type
    sensor_configs = {
        'cpu': {
            'name': 'Utilisation CPU',
            'device_type': 'cpu',
            'unit': '%',
            'get_value': lambda: psutil.cpu_percent(interval=1),
            'metadata': lambda: {'cores': psutil.cpu_count(), 'freq': psutil.cpu_freq().current if psutil.cpu_freq() else None}
        },
        'memory': {
            'name': 'Utilisation Mémoire',
            'device_type': 'memory',
            'unit': '%',
            'get_value': lambda: psutil.virtual_memory().percent,
            'metadata': lambda: {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'used': psutil.virtual_memory().used
            }
        },
        'disk': {
            'name': 'Utilisation Disque',
            'device_type': 'disk',
            'unit': '%',
            'get_value': lambda: psutil.disk_usage('/').percent,
            'metadata': lambda: {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free
            }
        },
        'network': {
            'name': 'Trafic Réseau',
            'device_type': 'network',
            'unit': 'bytes/s',
            'get_value': lambda: get_network_usage(),
            'metadata': lambda: get_network_stats()
        }
    }
    
    if sensor_type not in sensor_configs:
        messages.error(request, f"Type de capteur invalide: {sensor_type}")
        return redirect('staff_iot_devices')
    
    config = sensor_configs[sensor_type]
    
    # Créer ou récupérer l'appareil
    device, created = IoTDevice.objects.get_or_create(
        device_id=f'SYSTEM_{sensor_type.upper()}_SENSOR',
        defaults={
            'name': config['name'],
            'device_type': config['device_type'],
            'description': f'Capteur simulé de {config["name"].lower()}',
            'subject': subject,
            'created_by': staff,
            'status': 'active',
            'learning_objective': f"Analyser les tendances d'utilisation du {config['name'].lower()} et identifier les patterns d'utilisation",
            'expected_outcomes': "Comprendre les cycles d'utilisation et détecter les anomalies",
            'difficulty_level': 'intermediate'
        }
    )
    
    # Si l'appareil existe mais n'est pas lié à la bonne matière, le mettre à jour
    if device.subject != subject:
        device.subject = subject
        device.save()
    
    # Collecter les données
    value = config['get_value']()
    metadata = config['metadata']()
    
    # Ajouter la donnée
    IoTData.objects.create(
        device=device,
        value=value,
        unit=config['unit'],
        metadata=metadata
    )
    
    # Mettre à jour last_data_received
    device.last_data_received = timezone.now()
    device.save()
    
    messages.success(request, f'Donnée {config["name"]} ajoutée : {value:.1f}{config["unit"]}')
    return redirect('staff_iot_device_detail', device_id=device.id)

def get_network_usage():
    """Calcule l'utilisation réseau en bytes/s"""
    net_io = psutil.net_io_counters()
    time.sleep(1)  # Attendre 1 seconde
    net_io_2 = psutil.net_io_counters()
    
    bytes_sent = net_io_2.bytes_sent - net_io.bytes_sent
    bytes_recv = net_io_2.bytes_recv - net_io.bytes_recv
    return bytes_sent + bytes_recv

def get_network_stats():
    """Récupère les statistiques réseau"""
    net_io = psutil.net_io_counters()
    return {
        'bytes_sent': net_io.bytes_sent,
        'bytes_recv': net_io.bytes_recv,
        'packets_sent': net_io.packets_sent,
        'packets_recv': net_io.packets_recv,
        'errin': net_io.errin,
        'errout': net_io.errout,
        'dropin': net_io.dropin,
        'dropout': net_io.dropout
    }

@login_required
def api_iot_device_data(request, device_id):
    """API endpoint pour récupérer les données d'un appareil IoT avec des options d'agrégation"""
    device = get_object_or_404(IoTDevice, id=device_id)
    
    # Paramètres de l'API
    limit = int(request.GET.get('limit', 100))
    interval = request.GET.get('interval', 'raw')  # raw, minute, hour, day
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Construire la requête de base
    query = IoTData.objects.filter(device=device)
    
    # Appliquer les filtres de date si spécifiés
    if start_date:
        query = query.filter(timestamp__gte=start_date)
    if end_date:
        query = query.filter(timestamp__lte=end_date)
    
    # Agrégation des données selon l'intervalle
    if interval != 'raw':
        # Convertir en datetime pour l'agrégation
        query = query.annotate(
            interval_time=Trunc('timestamp', interval)
        ).values('interval_time').annotate(
            value=Avg('value'),
            count=Count('id')
        ).order_by('interval_time')
        
        labels = [d['interval_time'].strftime('%Y-%m-%d %H:%M:%S') for d in query[:limit]]
        values = [d['value'] for d in query[:limit]]
    else:
        # Données brutes
        data = query.order_by('-timestamp')[:limit]
        labels = [d.timestamp.strftime('%Y-%m-%d %H:%M:%S') for d in reversed(data)]
        values = [d.value for d in reversed(data)]
    
    # Récupérer les métadonnées du dernier point de données
    last_data = query.order_by('-timestamp').first()
    metadata = last_data.metadata if hasattr(last_data, 'metadata') else {}
    
    return JsonResponse({
        'labels': labels,
        'values': values,
        'unit': device.unit if hasattr(device, 'unit') else '',
        'metadata': metadata,
        'device_type': device.device_type,
        'device_name': device.name
    })
>>>>>>> develop
