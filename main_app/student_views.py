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
    for subject in subjects:
        attendance = Attendance.objects.filter(subject=subject)
        present_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=True, student=student).count()
        absent_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=False, student=student).count()
        subject_name.append(subject.name)
        data_present.append(present_count)
        data_absent.append(absent_count)
    context = {
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'total_subject': total_subject,
        'subjects': subjects,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': subject_name,
        'page_title': 'Student Homepage'

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
        'page_title': 'Student Feedback'

    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Feedback submitted for review")
                return redirect(reverse('student_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
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
        'page_title': "View Notifications"
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
