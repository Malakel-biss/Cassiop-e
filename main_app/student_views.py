import json
import math
from datetime import datetime
import os

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.db.models import Q

from .forms import *
from .models import *

def is_student(user):
    return user.user_type == '3'

def student_home(request):
    student = get_object_or_404(Student, admin=request.user)
    total_subject = Subject.objects.filter(course=student.course).count()
    total_attendance = AttendanceReport.objects.filter(student=student).count()
    total_present = AttendanceReport.objects.filter(student=student, status=True).count()
    if total_attendance == 0:  # Don't divide. DivisionByZero
        percent_absent = percent_present = 0
    else:
        percent_present = math.floor((total_present/total_attendance) * 100)
        percent_absent = math.ceil(100 - percent_present)
    subject_name = []
    data_present = []
    data_absent = []
    subjects = Subject.objects.filter(course=student.course)
    
    # Pour chaque matière, récupérer ou créer le suivi de progression
    progress_data = []
    subject_progress = []
    for subject in subjects:
        attendance = Attendance.objects.filter(subject=subject)
        present_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=True, student=student).count()
        absent_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=False, student=student).count()
        subject_name.append(subject.name)
        data_present.append(present_count)
        data_absent.append(absent_count)
        
        # Récupérer ou créer la progression pour cette matière
        progress, created = StudentProgress.objects.get_or_create(
            student=student,
            subject=subject
        )
        
        # Calculer la progression
        materials = CourseMaterial.objects.filter(subject=subject, is_visible=True)
        total_materials = materials.count()
        
        # Récupérer les devoirs de cette matière
        assignments = Assignment.objects.filter(subject=subject, is_active=True)
        total_assignments = assignments.count()
        
        # Total de ressources (matériels + devoirs)
        total_resources = total_materials + total_assignments
        
        if total_resources > 0:
            # Matériels complétés
            completed_materials = MaterialProgress.objects.filter(
                student=student,
                material__in=materials,
                is_completed=True
            ).count()
            
            # Devoirs soumis
            completed_assignments = AssignmentSubmission.objects.filter(
                student=student,
                assignment__in=assignments
            ).count()
            
            # Total complété
            total_completed = completed_materials + completed_assignments
            
            # Mettre à jour le pourcentage de progression
            progress_percent = (total_completed / total_resources) * 100
            progress.progress_percent = progress_percent
            
            # Mettre à jour le statut
            if progress_percent == 0:
                progress.status = 'not_started'
            elif progress_percent < 100:
                progress.status = 'in_progress'
            else:
                progress.status = 'completed'
            
            progress.save()
        
        # Ajouter aux données pour les graphiques
        progress_data.append({
            'subject': subject.name,
            'progress': progress.progress_percent,
            'status': progress.get_status_display(),
            'color': '#28a745' if progress.status == 'completed' else '#ffc107' if progress.status == 'in_progress' else '#dc3545'
        })
        
        subject_progress.append(progress.progress_percent)
    
    # Récupérer les devoirs/quiz à venir
    upcoming_assignments = Assignment.objects.filter(
        subject__in=subjects,
        is_active=True,
        due_date__gt=timezone.now()
    ).order_by('due_date')[:5]  # Limiter aux 5 prochains
    
    # Vérifier les soumissions pour ces devoirs
    assignments_with_status = []
    for assignment in upcoming_assignments:
        submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            student=student
        ).first()
        
        # Calculer le délai restant
        remaining_time = assignment.due_date - timezone.now()
        days_remaining = remaining_time.days
        hours_remaining = int(remaining_time.seconds / 3600)
        
        # État d'alerte basé sur le délai restant
        alert_level = 'success'  # Par défaut
        if not submission:
            if days_remaining < 1:
                alert_level = 'danger'
            elif days_remaining < 3:
                alert_level = 'warning'
        
        assignments_with_status.append({
            'assignment': assignment,
            'is_submitted': submission is not None,
            'days_remaining': days_remaining,
            'hours_remaining': hours_remaining,
            'alert_level': alert_level
        })
    
    # Calculer le temps d'étude recommandé pour chaque matière
    study_time_recommendations = []
    for subject in subjects:
        total_estimated_time = CourseMaterial.objects.filter(
            subject=subject, 
            is_visible=True
        ).aggregate(total=models.Sum('estimated_time'))['total'] or 0
        
        # Temps déjà passé
        time_spent = MaterialProgress.objects.filter(
            student=student,
            material__subject=subject
        ).aggregate(total=models.Sum('time_spent'))['total'] or 0
        
        # Temps restant
        remaining_time = max(0, total_estimated_time - time_spent)
        
        study_time_recommendations.append({
            'subject': subject.name,
            'total_time': total_estimated_time,
            'remaining_time': remaining_time,
            'time_spent': time_spent,
            'percent_complete': (time_spent / total_estimated_time * 100) if total_estimated_time > 0 else 0
        })
    
    # Analyse des devoirs soumis par matière
    assignment_stats = []
    for subject in subjects:
        total_assignments = Assignment.objects.filter(subject=subject, is_active=True).count()
        completed_assignments = AssignmentSubmission.objects.filter(
            student=student,
            assignment__subject=subject
        ).count()
        
        if total_assignments > 0:
            completion_rate = (completed_assignments / total_assignments) * 100
        else:
            completion_rate = 0
        
        assignment_stats.append({
            'subject': subject.name,
            'total': total_assignments,
            'completed': completed_assignments,
            'completion_rate': completion_rate
        })
    
    context = {
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'total_subject': total_subject,
        'subjects': subjects,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': subject_name,
        'page_title': 'Tableau de Bord Étudiant',
        'progress_data': progress_data,
        'subject_progress': subject_progress,
        'upcoming_assignments': assignments_with_status,
        'study_time_recommendations': study_time_recommendations,
        'assignment_stats': assignment_stats
    }
    return render(request, 'student_template/home_content.html', context)


@login_required(login_url='login')
@user_passes_test(is_student)
def student_view_attendance(request):
    student = get_object_or_404(Student, admin=request.user)
    attendance_reports = AttendanceReport.objects.filter(student=student).order_by('-attendance__date')
    
    context = {
        'attendance_reports': attendance_reports,
        'page_title': 'Voir les Présences'
    }
    return render(request, 'student_template/student_view_attendance.html', context)


def student_apply_leave(request):
    form = LeaveReportStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStudent.objects.filter(student=student),
        'page_title': 'Demande de Congé'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(request, "Votre demande de congé a été soumise pour examen")
                return redirect(reverse('student_apply_leave'))
            except Exception:
                messages.error(request, "Impossible de soumettre la demande")
        else:
            messages.error(request, "Le formulaire contient des erreurs!")
    return render(request, "student_template/student_apply_leave.html", context)


def student_feedback(request):
    form = FeedbackStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStudent.objects.filter(student=student),
        'page_title': 'Retour Étudiant'

    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Retour soumis pour examen")
                return redirect(reverse('student_feedback'))
            except Exception:
                messages.error(request, "Impossible de soumettre!")
        else:
            messages.error(request, "Le formulaire contient des erreurs!")
    return render(request, "student_template/student_feedback.html", context)


def student_view_profile(request):
    student = get_object_or_404(Student, admin=request.user)
    form = StudentEditForm(request.POST or None, instance=student)
    context = {
        'form': form,
        'student': student,
        'page_title': 'Mon Profil'
    }
    
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            address = request.POST.get('address')
            gender = request.POST.get('gender')
            password = request.POST.get('password')
            
            # Mise à jour des informations de base
            admin = student.admin
            admin.first_name = first_name
            admin.last_name = last_name
            admin.address = address
            admin.gender = gender
            
            # Gestion du mot de passe
            if password:
                admin.set_password(password)
            
            # Sauvegarde des modifications
            admin.save()
            student.save()
            
            messages.success(request, "Profil mis à jour avec succès!")
            return redirect(reverse('student_view_profile'))
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour du profil : {str(e)}")
    
    return render(request, "student_template/student_view_profile.html", context)


@csrf_exempt
def student_fcmtoken(request):
    token = request.POST.get('token')
    student_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        student_user.fcm_token = token
        student_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def student_view_notification(request):
    student = get_object_or_404(Student, admin=request.user)
    notifications = NotificationStudent.objects.filter(student=student)
    context = {
        'notifications': notifications,
        'page_title': "Voir les Notifications"
    }
    return render(request, "student_template/student_view_notification.html", context)


@login_required(login_url='login')
@user_passes_test(is_student)
def student_view_result(request):
    student = get_object_or_404(Student, admin=request.user)
    results = StudentResult.objects.filter(student=student)
    
    # Calculer le statut pour chaque résultat
    for result in results:
        total_score = float(result.exam) + float(result.test)
        result.status = "Validé" if total_score >= 10 else "Échoué"
        result.total_score = total_score
    
    context = {
        'results': results,
        'page_title': 'Mes Résultats'
    }
    return render(request, 'student_template/student_view_result.html', context)


@login_required(login_url='login')
@user_passes_test(is_student)
def student_course_materials(request):
    student = get_object_or_404(Student, admin=request.user)
    subjects = Subject.objects.filter(course=student.course)
    materials = CourseMaterial.objects.filter(subject__in=subjects, is_visible=True)
    
    context = {
        'materials': materials,
        'subjects': subjects,
        'page_title': 'Supports de Cours'
    }
    return render(request, 'student_template/student_course_materials.html', context)


@login_required(login_url='login')
@user_passes_test(is_student)
def student_assignments(request):
    student = get_object_or_404(Student, admin=request.user)
    subjects = Subject.objects.filter(course=student.course)
    assignments = Assignment.objects.filter(subject__in=subjects, is_active=True).order_by('-created_at')
    
    # Récupérer les soumissions existantes
    submissions = AssignmentSubmission.objects.filter(
        assignment__in=assignments,
        student=student
    )
    submission_dict = {sub.assignment.id: sub for sub in submissions}
    
    context = {
        'assignments': assignments,
        'submission_dict': submission_dict,
        'page_title': 'Quiz et Devoirs'
    }
    return render(request, 'student_template/student_assignments.html', context)

@login_required(login_url='login')
@user_passes_test(is_student)
def student_view_assignment(request, assignment_id):
    student = get_object_or_404(Student, admin=request.user)
    assignment = get_object_or_404(Assignment, id=assignment_id, subject__course=student.course)
    
    # Vérifier si l'étudiant a déjà soumis
    submission = AssignmentSubmission.objects.filter(
        assignment=assignment,
        student=student
    ).first()

    if request.method == 'POST':
        # Vérifier si la date limite n'est pas dépassée
        if assignment.due_date < timezone.now():
            messages.error(request, "La date limite est dépassée. Vous ne pouvez plus soumettre ou modifier votre travail.")
            return redirect('student_assignments')

        if assignment.assignment_type == 'quiz':
            # Traiter les réponses du quiz
            if submission:
                # Supprimer les anciennes réponses
                submission.answers.all().delete()
                
                # Créer les nouvelles réponses
                total_questions = assignment.questions.count()
                points_per_question = 20 / total_questions  # Points par question
                total_score = 0
                
                for question in assignment.questions.all():
                    answer_key = f'question_{question.id}'
                    if answer_key in request.POST:
                        answer_value = request.POST[answer_key]
                        is_correct = False
                        
                        if assignment.quiz_type == 'qcm':
                            # Pour les QCM, vérifier si le choix est correct
                            selected_choice = Choice.objects.get(id=answer_value)
                            is_correct = selected_choice.is_correct
                            QuizAnswer.objects.create(
                                submission=submission,
                                question=question,
                                selected_choice=selected_choice,
                                is_correct=is_correct
                            )
                        else:
                            # Pour les questions ouvertes, on ne peut pas corriger automatiquement
                            QuizAnswer.objects.create(
                                submission=submission,
                                question=question,
                                text_answer=answer_value
                            )
                        
                        if is_correct:
                            total_score += points_per_question
                
                # Mettre à jour le score
                submission.score = round(total_score, 2)
                submission.save()
                
                messages.success(request, f"Votre quiz a été mis à jour avec succès. Score : {submission.score}/20")
            else:
                # Créer une nouvelle soumission
                submission = AssignmentSubmission.objects.create(
                    assignment=assignment,
                    student=student,
                    submitted_at=timezone.now()
                )
                
                # Ajouter les réponses et calculer le score
                total_questions = assignment.questions.count()
                points_per_question = 20 / total_questions  # Points par question
                total_score = 0
                
                for question in assignment.questions.all():
                    answer_key = f'question_{question.id}'
                    if answer_key in request.POST:
                        answer_value = request.POST[answer_key]
                        is_correct = False
                        
                        if assignment.quiz_type == 'qcm':
                            # Pour les QCM, vérifier si le choix est correct
                            selected_choice = Choice.objects.get(id=answer_value)
                            is_correct = selected_choice.is_correct
                            QuizAnswer.objects.create(
                                submission=submission,
                                question=question,
                                selected_choice=selected_choice,
                                is_correct=is_correct
                            )
                        else:
                            # Pour les questions ouvertes, on ne peut pas corriger automatiquement
                            QuizAnswer.objects.create(
                                submission=submission,
                                question=question,
                                text_answer=answer_value
                            )
                        
                        if is_correct:
                            total_score += points_per_question
                
                # Mettre à jour le score
                submission.score = round(total_score, 2)
                submission.save()
                
                messages.success(request, f"Votre quiz a été soumis avec succès. Score : {submission.score}/20")
        else:
            # Traiter le fichier de devoir
            if 'file' not in request.FILES:
                messages.error(request, "Veuillez sélectionner un fichier à soumettre.")
                return redirect('student_view_assignment', assignment_id=assignment_id)

            file = request.FILES['file']
            
            # Vérifier le type de fichier
            allowed_types = ['application/pdf', 'application/msword', 
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                           'application/zip', 'application/x-rar-compressed']
            
            if file.content_type not in allowed_types:
                messages.error(request, "Type de fichier non autorisé. Formats acceptés : PDF, DOC, DOCX, ZIP, RAR")
                return redirect('student_view_assignment', assignment_id=assignment_id)
            
            # Vérifier la taille du fichier (max 10MB)
            if file.size > 10 * 1024 * 1024:  # 10MB en bytes
                messages.error(request, "Le fichier est trop volumineux. Taille maximale : 10MB")
                return redirect('student_view_assignment', assignment_id=assignment_id)

            try:
                if submission:
                    # Mettre à jour le fichier existant
                    if submission.submission_file:
                        # Supprimer l'ancien fichier
                        submission.submission_file.delete()
                    submission.submission_file = file
                    submission.submitted_at = timezone.now()
                    submission.save()
                    messages.success(request, "Votre devoir a été mis à jour avec succès.")
                else:
                    # Créer une nouvelle soumission
                    submission = AssignmentSubmission.objects.create(
                        assignment=assignment,
                        student=student,
                        submission_file=file,
                        submitted_at=timezone.now()
                    )
                    messages.success(request, "Votre devoir a été soumis avec succès.")
            except Exception as e:
                messages.error(request, f"Erreur lors de la soumission du fichier : {str(e)}")
                return redirect('student_view_assignment', assignment_id=assignment_id)

        return redirect('student_assignments')

    context = {
        'assignment': assignment,
        'submission': submission,
        'now': timezone.now(),
        'page_title': assignment.title
    }
    return render(request, 'student_template/student_view_assignment.html', context)

@login_required(login_url='login')
@user_passes_test(is_student)
def student_view_submission(request, submission_id):
    student = get_object_or_404(Student, admin=request.user)
    submission = get_object_or_404(AssignmentSubmission, id=submission_id, student=student)
    
    context = {
        'submission': submission,
        'page_title': f'Soumission - {submission.assignment.title}'
    }
    return render(request, 'student_template/student_view_submission.html', context)

# Messagerie
@login_required(login_url='login')
@user_passes_test(is_student)
def student_inbox(request):
    student = get_object_or_404(Student, admin=request.user)
    messages_received = Message.objects.filter(receiver=student.admin)
    
    # Marquer comme lus les messages ouverts
    if 'message_id' in request.GET:
        message_id = request.GET.get('message_id')
        message = get_object_or_404(Message, id=message_id, receiver=student.admin)
        message.is_read = True
        message.save()
    
    context = {
        'messages': messages_received,
        'page_title': 'Messagerie - Boîte de réception'
    }
    return render(request, 'student_template/student_inbox.html', context)

@login_required(login_url='login')
@user_passes_test(is_student)
def student_sent_messages(request):
    student = get_object_or_404(Student, admin=request.user)
    messages_sent = Message.objects.filter(sender=student.admin)
    
    context = {
        'messages': messages_sent,
        'page_title': 'Messagerie - Messages envoyés'
    }
    return render(request, 'student_template/student_sent_messages.html', context)

@login_required(login_url='login')
@user_passes_test(is_student)
def student_compose_message(request):
    student = get_object_or_404(Student, admin=request.user)
    course = student.course
    
    # Récupérer les professeurs qui enseignent dans la filière de l'étudiant
    staff_members = Staff.objects.filter(course=course)
    
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver')
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        attachment = request.FILES.get('attachment', None)
        
        if not receiver_id or not subject or not content:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return redirect('student_compose_message')
        
        try:
            receiver = CustomUser.objects.get(id=receiver_id)
            
            # Créer le message
            message = Message(
                sender=student.admin,
                receiver=receiver,
                subject=subject,
                content=content,
                attachment=attachment
            )
            message.save()
            
            messages.success(request, "Message envoyé avec succès.")
            return redirect('student_sent_messages')
            
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
    
    context = {
        'staff_members': staff_members,
        'page_title': 'Composer un message'
    }
    return render(request, 'student_template/student_compose_message.html', context)

@login_required(login_url='login')
@user_passes_test(is_student)
def student_view_message(request, message_id):
    student = get_object_or_404(Student, admin=request.user)
    
    # Utiliser filter et get au lieu de get_object_or_404 avec Q
    try:
        message = Message.objects.filter(
            id=message_id
        ).filter(
            Q(sender=student.admin) | Q(receiver=student.admin)
        ).get()
    except Message.DoesNotExist:
        messages.error(request, "Message non trouvé.")
        return redirect('student_inbox')
    
    # Marquer comme lu si c'est un message reçu
    if message.receiver == student.admin and not message.is_read:
        message.is_read = True
        message.save()
    
    context = {
        'message': message,
        'page_title': f'Message - {message.subject}'
    }
    return render(request, 'student_template/student_view_message.html', context)

# Forums
@login_required(login_url='login')
@user_passes_test(is_student)
def student_forum_categories(request):
    student = get_object_or_404(Student, admin=request.user)
    
    # Récupérer les catégories générales et celles de la filière de l'étudiant
    categories = ForumCategory.objects.filter(
        Q(course__isnull=True) | Q(course=student.course)
    )
    
    context = {
        'categories': categories,
        'page_title': 'Forums de discussion'
    }
    return render(request, 'student_template/student_forum_categories.html', context)

@login_required(login_url='login')
@user_passes_test(is_student)
def student_forum_topics(request, category_id):
    student = get_object_or_404(Student, admin=request.user)
    
    # Utiliser filter et get au lieu de get_object_or_404 avec Q
    try:
        category = ForumCategory.objects.filter(
            id=category_id
        ).filter(
            Q(course__isnull=True) | Q(course=student.course)
        ).get()
    except ForumCategory.DoesNotExist:
        messages.error(request, "Catégorie non trouvée ou vous n'avez pas accès à cette catégorie.")
        return redirect('student_forum_categories')
    
    topics = ForumTopic.objects.filter(category=category)
    
    context = {
        'category': category,
        'topics': topics,
        'page_title': f'Forum - {category.name}'
    }
    return render(request, 'student_template/student_forum_topics.html', context)

@login_required(login_url='login')
@user_passes_test(is_student)
def student_forum_topic_detail(request, topic_id):
    student = get_object_or_404(Student, admin=request.user)
    topic = get_object_or_404(ForumTopic, id=topic_id)
    
    # Vérifier que l'étudiant a accès à ce sujet
    if not (topic.category.course is None or topic.category.course == student.course):
        messages.error(request, "Vous n'avez pas accès à ce sujet.")
        return redirect('student_forum_categories')
    
    # Incrémenter le compteur de vues
    topic.views += 1
    topic.save()
    
    replies = ForumReply.objects.filter(topic=topic)
    
    if request.method == 'POST' and not topic.is_closed:
        content = request.POST.get('content')
        
        if content:
            reply = ForumReply(
                topic=topic,
                content=content,
                created_by=student.admin
            )
            reply.save()
            
            messages.success(request, "Votre réponse a été publiée.")
            return redirect('student_forum_topic_detail', topic_id=topic.id)
        else:
            messages.error(request, "Le contenu de la réponse ne peut pas être vide.")
    
    context = {
        'topic': topic,
        'replies': replies,
        'page_title': topic.title
    }
    return render(request, 'student_template/student_forum_topic_detail.html', context)

@login_required(login_url='login')
@user_passes_test(is_student)
def student_create_topic(request, category_id):
    student = get_object_or_404(Student, admin=request.user)
    
    # Utiliser filter et get au lieu de get_object_or_404 avec Q
    try:
        category = ForumCategory.objects.filter(
            id=category_id
        ).filter(
            Q(course__isnull=True) | Q(course=student.course)
        ).get()
    except ForumCategory.DoesNotExist:
        messages.error(request, "Catégorie non trouvée ou vous n'avez pas accès à cette catégorie.")
        return redirect('student_forum_categories')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if title and content:
            topic = ForumTopic(
                title=title,
                content=content,
                category=category,
                created_by=student.admin
            )
            topic.save()
            
            messages.success(request, "Votre sujet a été créé avec succès.")
            return redirect('student_forum_topic_detail', topic_id=topic.id)
        else:
            messages.error(request, "Veuillez remplir tous les champs.")
    
    context = {
        'category': category,
        'page_title': 'Créer un nouveau sujet'
    }
    return render(request, 'student_template/student_create_topic.html', context)

@login_required(login_url='login')
@user_passes_test(is_student)
def student_colab_notebooks(request):
    """Vue pour afficher la liste des notebooks Google Colab disponibles pour l'étudiant."""
    student = get_object_or_404(Student, admin=request.user)
    
    # Récupérer les notebooks liés aux sujets des cours de l'étudiant
    notebooks = GoogleColabNotebook.objects.filter(
        subject__course=student.course,
        is_visible=True
    ).order_by('-created_at')
    
    # Récupérer les progrès de l'étudiant pour chaque notebook
    student_progress = {}
    for notebook in notebooks:
        progress, created = ColabNotebookProgress.objects.get_or_create(
            student=student,
            notebook=notebook,
            defaults={
                'progress_percent': 0,
                'is_completed': False
            }
        )
        # Utiliser l'ID du notebook comme clé (int)
        student_progress[notebook.id] = progress
    
    context = {
        'notebooks': notebooks,
        'student_progress': student_progress,
        'page_title': 'Exercices Google Colab'
    }
    return render(request, 'student_template/student_colab_notebooks.html', context)

@login_required(login_url='login')
@user_passes_test(is_student)
def student_view_colab_notebook(request, notebook_id):
    """Vue pour afficher et utiliser un notebook Google Colab spécifique."""
    student = get_object_or_404(Student, admin=request.user)
    notebook = get_object_or_404(GoogleColabNotebook, id=notebook_id, is_visible=True)
    
    # Vérifier que le notebook appartient bien au cours de l'étudiant
    if notebook.subject.course != student.course:
        messages.error(request, "Vous n'êtes pas autorisé à accéder à ce notebook")
        return redirect('student_colab_notebooks')
    
    # Récupérer ou créer le suivi de progression
    progress, created = ColabNotebookProgress.objects.get_or_create(
        student=student,
        notebook=notebook,
        defaults={
            'progress_percent': 0,
            'is_completed': False
        }
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'duplicate':
            # Créer l'URL de duplication en ajoutant "copy" à l'URL du template
            template_url = notebook.colab_url
            if 'colab.research.google.com' in template_url:
                if not template_url.endswith('/copy'):
                    duplicate_url = template_url + '/copy'
                else:
                    duplicate_url = template_url
                return redirect(duplicate_url)
            else:
                messages.error(request, "URL de notebook invalide")
                
        elif action == 'save_url':
            personal_url = request.POST.get('personal_url')
            if personal_url and 'colab.research.google.com' in personal_url:
                progress.personal_colab_url = personal_url
                progress.save()
                messages.success(request, "URL de votre notebook personnel enregistrée avec succès")
            else:
                messages.error(request, "Veuillez fournir une URL Google Colab valide")
                
        elif action == 'complete':
            progress.is_completed = True
            progress.completed_date = timezone.now()
            progress.save()
            messages.success(request, "Exercice marqué comme terminé")
            
        elif action == 'update_progress':
            new_progress = request.POST.get('progress', 0)
            try:
                new_progress = int(new_progress)
                if 0 <= new_progress <= 100:
                    progress.progress_percent = new_progress
                    progress.save()
                    messages.success(request, "Progression mise à jour")
                else:
                    messages.error(request, "La progression doit être entre 0 et 100")
            except ValueError:
                messages.error(request, "Valeur de progression invalide")
    
    context = {
        'notebook': notebook,
        'progress': progress,
        'page_title': notebook.title
    }
    return render(request, 'student_template/student_view_colab_notebook.html', context)

@login_required(login_url='login')
@user_passes_test(is_student)
def student_update_colab_progress(request, notebook_id):
    """Vue pour mettre à jour la progression d'un étudiant sur un notebook."""
    if request.method != 'POST':
        messages.error(request, "Méthode non autorisée")
        return redirect('student_colab_notebooks')
    
    student = get_object_or_404(Student, admin=request.user)
    notebook = get_object_or_404(GoogleColabNotebook, id=notebook_id)
    
    # Vérifier que le notebook appartient bien au cours de l'étudiant
    if notebook.subject.course != student.course:
        messages.error(request, "Vous n'êtes pas autorisé à accéder à ce notebook")
        return redirect('student_colab_notebooks')
    
    progress_percent = request.POST.get('progress_percent')
    is_completed = request.POST.get('is_completed') == 'true'
    notes = request.POST.get('notes', '')
    
    try:
        progress_percent = float(progress_percent)
        if progress_percent < 0 or progress_percent > 100:
            messages.error(request, "Le pourcentage de progression doit être entre 0 et 100")
            return redirect('student_view_colab_notebook', notebook_id=notebook.id)
    except ValueError:
        messages.error(request, "Valeur de progression invalide")
        return redirect('student_view_colab_notebook', notebook_id=notebook.id)
    
    # Mettre à jour la progression
    progress, created = ColabNotebookProgress.objects.get_or_create(
        student=student,
        notebook=notebook,
        defaults={
            'progress_percent': 0,
            'is_completed': False
        }
    )
    
    progress.progress_percent = progress_percent
    progress.is_completed = is_completed
    progress.notes = notes
    
    if is_completed and not progress.completed_date:
        progress.completed_date = timezone.now()
    
    progress.save()
    
    messages.success(request, "Progression mise à jour avec succès")
    return redirect('student_view_colab_notebook', notebook_id=notebook.id)
