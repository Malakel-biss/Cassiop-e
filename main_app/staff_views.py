import json

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
import os, json
from main_app.ai_assistant.transcript import generate_transcript



import os

# Update staff_views.py to handle PDF text extraction
from main_app.ai_assistant.pdf_parser import extract_text_from_pdf

@login_required
def add_lesson(request):
    if request.method == "POST":
        module_id = request.POST.get("module")
        name = request.POST.get("name")
        pdf = request.FILES.get("pdf")
        video = request.FILES.get("video")

        try:
            module = Module.objects.get(id=module_id)
            lesson = Lesson.objects.create(
                module=module,
                name=name,
                pdf=pdf,
                video=video
            )

            # Step 1: Extract PDF text if a PDF is uploaded
            if lesson.pdf:
                pdf_path = lesson.pdf.path
                pdf_text = extract_text_from_pdf(pdf_path)
                if pdf_text:
                    lesson.pdf_text = pdf_text  # Save extracted PDF text to DB
                    lesson.save()
                    print(f"✅ PDF text saved for lesson {lesson.id}")

            # Step 2: Continue with video transcription (as before)
            if lesson.video:
                video_path = lesson.video.path
                transcript_text = generate_transcript(video_path, lesson.id)  # Save plain text

                if transcript_text:
                    lesson.transcript = transcript_text  # Save plain transcript to DB
                    lesson.save()

                    # Step 3: Save the JSON transcript in DB
                    json_path = os.path.join("media", "transcripts", f"{lesson.id}_transcript.json")
                    with open(json_path, "r", encoding="utf-8") as f:
                        transcript_json = json.load(f)
                        lesson.transcript_json = transcript_json  # Save JSON in DB
                        lesson.save()

                    print(f"✅ Transcript and JSON saved to DB for lesson {lesson.id}")

            messages.success(request, "Leçon ajoutée avec succès.")

        except Module.DoesNotExist:
            messages.error(request, "Module invalide.")

        return redirect("add_lesson")

    modules = Module.objects.all()
    return render(request, "main_app/add_lesson.html", {"modules": modules})


def staff_add_course_material(request):
    if request.method == "POST":
        form = CourseMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.staff = request.user
            material.save()

            # 🔥 Transcript generation
            video_path = material.video.path  # or material.file.path
            transcript = generate_transcript(video_path)

            if transcript:
                transcript_dir = os.path.join("data", "transcripts")
                os.makedirs(transcript_dir, exist_ok=True)
                transcript_path = os.path.join(transcript_dir, f"{material.id}.json")

                with open(transcript_path, "w", encoding="utf-8") as f:
                    json.dump(
                        [{"start": 0, "end": 9999, "text": transcript}],
                        f,
                        indent=2,
                        ensure_ascii=False
                    )
                print("✅ Transcript saved for video:", material.id)

            return redirect("some_success_view")

    else:
        form = CourseMaterialForm()

    return render(request, "staff_template/staff_add_course_material.html", {"form": form})


from .forms import *
from .models import *

def is_staff(user):
    return user.user_type == '2'

def staff_home(request):
    staff = get_object_or_404(Staff, admin=request.user)
    total_students = Student.objects.filter(course=staff.course).count()
    total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
    subjects = Subject.objects.filter(staff=staff)
    total_subject = subjects.count()
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name)
        attendance_list.append(attendance_count)
    context = {
        'page_title': 'Tableau de Bord - ' + str(staff.admin.last_name) + ' (' + str(staff.course) + ')',
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list
    }
    return render(request, 'staff_template/home_content.html', context)


def staff_take_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Prendre la Présence'
    }

    return render(request, 'staff_template/staff_take_attendance.html', context)


@csrf_exempt
def get_students(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        students = Student.objects.filter(
            course_id=subject.course.id, session=session)
        student_data = []
        for student in students:
            data = {
                    "id": student.id,
                    "name": student.admin.last_name + " " + student.admin.first_name
                    }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e



@csrf_exempt
def save_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    students = json.loads(student_data)
    try:
        session = get_object_or_404(Session, id=session_id)
        subject = get_object_or_404(Subject, id=subject_id)

        # Check if an attendance object already exists for the given date and session
        attendance, created = Attendance.objects.get_or_create(session=session, subject=subject, date=date)

        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))

            # Check if an attendance report already exists for the student and the attendance object
            attendance_report, report_created = AttendanceReport.objects.get_or_create(student=student, attendance=attendance)

            # Update the status only if the attendance report was newly created
            if report_created:
                attendance_report.status = student_dict.get('status')
                attendance_report.save()

    except Exception as e:
        return None

    return HttpResponse("OK")


def staff_update_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Mettre à Jour la Présence'
    }

    return render(request, 'staff_template/staff_update_attendance.html', context)


@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=date)
        student_data = []
        for attendance in attendance_data:
            data = {"id": attendance.student.admin.id,
                    "name": attendance.student.admin.last_name + " " + attendance.student.admin.first_name,
                    "status": attendance.status}
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def update_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    students = json.loads(student_data)
    try:
        attendance = get_object_or_404(Attendance, id=date)

        for student_dict in students:
            student = get_object_or_404(
                Student, admin_id=student_dict.get('id'))
            attendance_report = get_object_or_404(AttendanceReport, student=student, attendance=attendance)
            attendance_report.status = student_dict.get('status')
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")


def staff_apply_leave(request):
    form = LeaveReportStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStaff.objects.filter(staff=staff),
        'page_title': 'Demander un Congé'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(
                    request, "Votre demande de congé a été soumise pour examen")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Impossible de soumettre la demande!")
        else:
            messages.error(request, "Le formulaire contient des erreurs!")
    return render(request, "staff_template/staff_apply_leave.html", context)


def staff_feedback(request):
    form = FeedbackStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStaff.objects.filter(staff=staff),
        'page_title': 'Ajouter un Retour'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Retour soumis pour examen")
                return redirect(reverse('staff_feedback'))
            except Exception:
                messages.error(request, "Impossible de soumettre le retour!")
        else:
            messages.error(request, "Le formulaire contient des erreurs!")
    return render(request, "staff_template/staff_feedback.html", context)


def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    form = StaffEditForm(request.POST or None, request.FILES or None,instance=staff)
    context = {'form': form, 'page_title': 'Voir/Modifier Profil'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = staff.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                staff.save()
                messages.success(request, "Profil mis à jour!")
                return redirect(reverse('staff_view_profile'))
            else:
                messages.error(request, "Données invalides")
                return render(request, "staff_template/staff_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Erreur lors de la mise à jour du profil " + str(e))
            return render(request, "staff_template/staff_view_profile.html", context)

    return render(request, "staff_template/staff_view_profile.html", context)


@csrf_exempt
def staff_fcmtoken(request):
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def staff_view_notification(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff)
    context = {
        'notifications': notifications,
        'page_title': "Voir les Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)


def staff_add_result(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    sessions = Session.objects.all()
    context = {
        'page_title': 'Ajouter un Résultat',
        'subjects': subjects,
        'sessions': sessions
    }
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list')
            subject_id = request.POST.get('subject')
            test = request.POST.get('test')
            exam = request.POST.get('exam')
            student = get_object_or_404(Student, id=student_id)
            subject = get_object_or_404(Subject, id=subject_id)
            try:
                data = StudentResult.objects.get(
                    student=student, subject=subject)
                data.exam = exam
                data.test = test
                data.save()
                messages.success(request, "Notes mises à jour avec succès")
            except:
                result = StudentResult(student=student, subject=subject, test=test, exam=exam)
                result.save()
                messages.success(request, "Notes enregistrées avec succès")
        except Exception as e:
            messages.warning(request, "Erreur lors du traitement du formulaire")
    return render(request, "staff_template/staff_add_result.html", context)


@csrf_exempt
def fetch_student_result(request):
    try:
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)
        result = StudentResult.objects.get(student=student, subject=subject)
        result_data = {
            'exam': result.exam,
            'test': result.test
        }
        return HttpResponse(json.dumps(result_data))
    except Exception as e:
        return HttpResponse('False')


@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_course_materials(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    materials = CourseMaterial.objects.filter(subject__in=subjects)
    
    context = {
        'materials': materials,
        'subjects': subjects,
        'page_title': 'Supports de Cours'
    }
    return render(request, 'staff_template/staff_course_materials.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_add_course_material(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    
    if request.method == 'POST':
        try:
            subject_id = request.POST.get('subject')
            title = request.POST.get('title')
            description = request.POST.get('description')
            material_type = request.POST.get('material_type')
            file = request.FILES.get('file')
            
            if not file:
                messages.error(request, "Veuillez sélectionner un fichier")
                return redirect('staff_add_course_material')
            
            subject = get_object_or_404(Subject, id=subject_id)
            
            # Vérifier que le sujet appartient bien au professeur
            if subject.staff != staff:
                messages.error(request, "Vous n'êtes pas autorisé à ajouter des supports pour ce module")
                return redirect('staff_add_course_material')
            
            # Créer le support de cours
            material = CourseMaterial(
                subject=subject,
                title=title,
                description=description,
                material_type=material_type,
                file=file,
                is_visible=True,
                uploaded_by=request.user
            )
            material.save()
            
            messages.success(request, "Support de cours ajouté avec succès")
            return redirect('staff_course_materials')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout du support : {str(e)}")
    
    context = {
        'subjects': subjects,
        'page_title': 'Ajouter un Support de Cours'
    }
    return render(request, 'staff_template/staff_add_course_material.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_delete_course_material(request, material_id):
    material = get_object_or_404(CourseMaterial, id=material_id)
    if material.uploaded_by == request.user:
        material.delete()
        messages.success(request, "Support de cours supprimé avec succès!")
    else:
        messages.error(request, "Vous n'avez pas la permission de supprimer ce support.")
    return redirect('staff_course_materials')

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_edit_course_material(request, material_id):
    staff = get_object_or_404(Staff, admin=request.user)
    material = get_object_or_404(CourseMaterial, id=material_id, subject__staff=staff)
    subjects = Subject.objects.filter(staff=staff)
    
    if request.method == 'POST':
        try:
            subject_id = request.POST.get('subject')
            title = request.POST.get('title')
            description = request.POST.get('description')
            material_type = request.POST.get('material_type')
            file = request.FILES.get('file')
            
            subject = get_object_or_404(Subject, id=subject_id)
            
            # Vérifier que le sujet appartient bien au professeur
            if subject.staff != staff:
                messages.error(request, "Vous n'êtes pas autorisé à modifier ce support")
                return redirect('staff_course_materials')
            
            # Mettre à jour le support
            material.subject = subject
            material.title = title
            material.description = description
            material.material_type = material_type
            
            # Mettre à jour le fichier seulement si un nouveau est fourni
            if file:
                material.file = file
            
            material.save()
            messages.success(request, "Support de cours modifié avec succès")
            return redirect('staff_course_materials')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification du support : {str(e)}")
    
    context = {
        'material': material,
        'subjects': subjects,
        'page_title': 'Modifier le Support de Cours'
    }
    return render(request, 'staff_template/staff_edit_course_material.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_assignments(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    assignments = Assignment.objects.filter(subject__in=subjects).order_by('-created_at')
    
    context = {
        'assignments': assignments,
        'subjects': subjects,
        'page_title': 'Gestion des Quiz et Devoirs'
    }
    return render(request, 'staff_template/staff_assignments.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_add_assignment(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        subject_id = request.POST.get('subject')
        due_date = request.POST.get('due_date')
        assignment_type = request.POST.get('assignment_type')
        quiz_type = request.POST.get('quiz_type')
        support_file = request.FILES.get('support_file')
        total_points = request.POST.get('total_points', 20)

        try:
            subject = Subject.objects.get(id=subject_id)
            assignment = Assignment.objects.create(
                title=title,
                description=description,
                subject=subject,
                due_date=due_date,
                assignment_type=assignment_type,
                quiz_type=quiz_type if assignment_type == 'quiz' else None,
                support_file=support_file,
                total_points=total_points
            )

            if assignment_type == 'quiz':
                questions = request.POST.getlist('questions[]')
                for i, question_text in enumerate(questions):
                    if question_text.strip():
                        question = Question.objects.create(
                            assignment=assignment,
                            text=question_text,
                            order=i
                        )
                        
                        if quiz_type == 'qcm':
                            choices = request.POST.getlist(f'choices_{i}[]')
                            correct_choice = int(request.POST.get(f'correct_choice_{i}', 0))
                            
                            for j, choice_text in enumerate(choices):
                                if choice_text.strip():
                                    Choice.objects.create(
                                        question=question,
                                        text=choice_text,
                                        is_correct=(j == correct_choice)
                                    )

            messages.success(request, 'Quiz/Devoir ajouté avec succès!')
            return redirect('staff_assignments')
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout: {str(e)}')
    else:
        subjects = Subject.objects.filter(staff__admin=request.user)
        return render(request, 'staff_template/staff_add_assignment.html', {
            'subjects': subjects,
            'page_title': 'Ajouter un Quiz/Devoir'
        })

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_view_submissions(request, assignment_id):
    staff = get_object_or_404(Staff, admin=request.user)
    assignment = get_object_or_404(Assignment, id=assignment_id, subject__staff=staff)
    submissions = AssignmentSubmission.objects.filter(assignment=assignment).order_by('submitted_at')
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
        'page_title': f'Soumissions - {assignment.title}'
    }
    return render(request, 'staff_template/staff_view_submissions.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_grade_submission(request, submission_id):
    staff = get_object_or_404(Staff, admin=request.user)
    submission = get_object_or_404(AssignmentSubmission, id=submission_id, assignment__subject__staff=staff)
    
    if request.method == 'POST':
        try:
            score = request.POST.get('score')
            feedback = request.POST.get('feedback')
            
            submission.score = score
            submission.feedback = feedback
            submission.save()
            
            if submission.assignment.assignment_type == 'quiz':
                answers = request.POST.getlist('answers[]')
                for i, answer in enumerate(answers):
                    quiz_answer = submission.answers.all()[i]
                    quiz_answer.is_correct = (answer == 'true')
                    quiz_answer.save()
            
            messages.success(request, "Note et feedback enregistrés avec succès!")
            return redirect('staff_view_submissions', assignment_id=submission.assignment.id)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la notation: {str(e)}")
    
    context = {
        'submission': submission,
        'page_title': f'Noter - {submission.student.admin.get_full_name()}'
    }
    return render(request, 'staff_template/staff_grade_submission.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def toggle_assignment_status(request, assignment_id):
    if request.method == 'POST':
        try:
            assignment = get_object_or_404(Assignment, id=assignment_id, subject__staff__admin=request.user)
            assignment.is_active = not assignment.is_active
            assignment.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_dashboard(request):
    staff = get_object_or_404(Staff, admin=request.user)
    total_students = Student.objects.filter(course=staff.course).count()
    total_subjects = Subject.objects.filter(staff=staff).count()
    total_assignments = Assignment.objects.filter(subject__staff=staff).count()
    total_submissions = AssignmentSubmission.objects.filter(assignment__subject__staff=staff).count()
    assignments = Assignment.objects.filter(subject__staff=staff).order_by('-created_at')[:10]
    
    from django.utils import timezone
    now = timezone.now()
    
    context = {
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'assignments': assignments,
        'now': now,
        'page_title': 'Tableau de bord'
    }
    return render(request, 'staff_template/staff_dashboard.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_inbox(request):
    staff = get_object_or_404(Staff, admin=request.user)
    messages_received = Message.objects.filter(receiver=staff.admin)
    
    # Marquer comme lus les messages ouverts
    if 'message_id' in request.GET:
        message_id = request.GET.get('message_id')
        message = get_object_or_404(Message, id=message_id, receiver=staff.admin)
        message.is_read = True
        message.save()
    
    context = {
        'messages': messages_received,
        'page_title': 'Messagerie - Boîte de réception'
    }
    return render(request, 'staff_template/staff_inbox.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_sent_messages(request):
    staff = get_object_or_404(Staff, admin=request.user)
    messages_sent = Message.objects.filter(sender=staff.admin)
    
    context = {
        'messages': messages_sent,
        'page_title': 'Messagerie - Messages envoyés'
    }
    return render(request, 'staff_template/staff_sent_messages.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_compose_message(request):
    staff = get_object_or_404(Staff, admin=request.user)
    course = staff.course
    
    # Récupérer les étudiants de la filière du professeur
    students = Student.objects.filter(course=course)
    
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver')
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        attachment = request.FILES.get('attachment', None)
        
        if not receiver_id or not subject or not content:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return redirect('staff_compose_message')
        
        try:
            receiver = CustomUser.objects.get(id=receiver_id)
            
            # Créer le message
            message = Message(
                sender=staff.admin,
                receiver=receiver,
                subject=subject,
                content=content,
                attachment=attachment
            )
            message.save()
            
            messages.success(request, "Message envoyé avec succès.")
            return redirect('staff_sent_messages')
            
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
    
    context = {
        'students': students,
        'page_title': 'Composer un message'
    }
    return render(request, 'staff_template/staff_compose_message.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_view_message(request, message_id):
    staff = get_object_or_404(Staff, admin=request.user)
    
    # Utiliser filter et get au lieu de get_object_or_404 avec Q
    try:
        message = Message.objects.filter(
            id=message_id
        ).filter(
            Q(sender=staff.admin) | Q(receiver=staff.admin)
        ).get()
    except Message.DoesNotExist:
        messages.error(request, "Message non trouvé.")
        return redirect('staff_inbox')
    
    # Marquer comme lu si c'est un message reçu
    if message.receiver == staff.admin and not message.is_read:
        message.is_read = True
        message.save()
    
    context = {
        'message': message,
        'page_title': f'Message - {message.subject}'
    }
    return render(request, 'staff_template/staff_view_message.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_forum_categories(request):
    staff = get_object_or_404(Staff, admin=request.user)
    
    # Récupérer les catégories générales et celles de la filière du professeur
    categories = ForumCategory.objects.filter(
        Q(course__isnull=True) | Q(course=staff.course)
    )
    
    context = {
        'categories': categories,
        'page_title': 'Forums de discussion'
    }
    return render(request, 'staff_template/staff_forum_categories.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_forum_topics(request, category_id):
    staff = get_object_or_404(Staff, admin=request.user)
    
    # Utiliser filter et get au lieu de get_object_or_404 avec Q
    try:
        category = ForumCategory.objects.filter(
            id=category_id
        ).filter(
            Q(course__isnull=True) | Q(course=staff.course)
        ).get()
    except ForumCategory.DoesNotExist:
        messages.error(request, "Catégorie non trouvée ou vous n'avez pas accès à cette catégorie.")
        return redirect('staff_forum_categories')
    
    topics = ForumTopic.objects.filter(category=category)
    
    context = {
        'category': category,
        'topics': topics,
        'page_title': f'Forum - {category.name}'
    }
    return render(request, 'staff_template/staff_forum_topics.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_forum_topic_detail(request, topic_id):
    staff = get_object_or_404(Staff, admin=request.user)
    topic = get_object_or_404(ForumTopic, id=topic_id)
    
    # Vérifier que le professeur a accès à ce sujet
    if not (topic.category.course is None or topic.category.course == staff.course):
        messages.error(request, "Vous n'avez pas accès à ce sujet.")
        return redirect('staff_forum_categories')
    
    # Incrémenter le compteur de vues
    topic.views += 1
    topic.save()
    
    replies = ForumReply.objects.filter(topic=topic)
    
    if request.method == 'POST' and not topic.is_closed:
        content = request.POST.get('content')
        mark_as_solution = request.POST.get('mark_solution', False)
        
        if content:
            reply = ForumReply(
                topic=topic,
                content=content,
                created_by=staff.admin,
                is_solution=mark_as_solution
            )
            reply.save()
            
            if mark_as_solution:
                # Optionnel: Fermer le sujet si une solution a été marquée
                topic.is_closed = True
                topic.save()
                messages.success(request, "Votre réponse a été publiée comme solution. Le sujet est maintenant fermé.")
            else:
                messages.success(request, "Votre réponse a été publiée.")
                
            return redirect('staff_forum_topic_detail', topic_id=topic.id)
        else:
            messages.error(request, "Le contenu de la réponse ne peut pas être vide.")
    
    context = {
        'topic': topic,
        'replies': replies,
        'page_title': topic.title,
        'is_staff': True  # Pour indiquer que c'est un professeur qui voit la page
    }
    return render(request, 'staff_template/staff_forum_topic_detail.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_create_topic(request, category_id):
    staff = get_object_or_404(Staff, admin=request.user)
    
    # Utiliser filter et get au lieu de get_object_or_404 avec Q
    try:
        category = ForumCategory.objects.filter(
            id=category_id
        ).filter(
            Q(course__isnull=True) | Q(course=staff.course)
        ).get()
    except ForumCategory.DoesNotExist:
        messages.error(request, "Catégorie non trouvée ou vous n'avez pas accès à cette catégorie.")
        return redirect('staff_forum_categories')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        is_pinned = request.POST.get('is_pinned', False)
        
        if title and content:
            topic = ForumTopic(
                title=title,
                content=content,
                category=category,
                created_by=staff.admin,
                is_pinned=is_pinned
            )
            topic.save()
            
            messages.success(request, "Votre sujet a été créé avec succès.")
            return redirect('staff_forum_topic_detail', topic_id=topic.id)
        else:
            messages.error(request, "Veuillez remplir tous les champs.")
    
    context = {
        'category': category,
        'page_title': 'Créer un nouveau sujet',
        'is_staff': True
    }
    return render(request, 'staff_template/staff_create_topic.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_manage_forum_category(request):
    staff = get_object_or_404(Staff, admin=request.user)
    
    # Les professeurs peuvent créer des catégories pour leur cours
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        course_id = request.POST.get('course')
        
        if name and description:
            if course_id:
                course = get_object_or_404(Course, id=course_id)
                # Vérifier que le professeur appartient à ce cours
                if course != staff.course:
                    messages.error(request, "Vous ne pouvez créer des catégories que pour votre filière.")
                    return redirect('staff_manage_forum_category')
            else:
                course = None
                
            category = ForumCategory(
                name=name,
                description=description,
                course=course
            )
            category.save()
            
            messages.success(request, "Catégorie créée avec succès.")
            return redirect('staff_forum_categories')
        else:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
    
    # Récupérer les catégories existantes que le professeur peut gérer
    categories = ForumCategory.objects.filter(course=staff.course)
    
    context = {
        'categories': categories,
        'course': staff.course,
        'page_title': 'Gérer les catégories du forum'
    }
    return render(request, 'staff_template/staff_manage_forum_category.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_colab_notebooks(request):
    """Vue pour afficher la liste des notebooks Google Colab créés par le professeur."""
    staff = get_object_or_404(Staff, admin=request.user)
    notebooks = GoogleColabNotebook.objects.filter(created_by=staff)
    subjects = Subject.objects.filter(staff=staff)
    
    context = {
        'notebooks': notebooks,
        'subjects': subjects,
        'page_title': 'Exercices Google Colab'
    }
    return render(request, 'staff_template/staff_colab_notebooks.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_add_colab_notebook(request):
    """Vue pour ajouter un nouveau notebook Google Colab."""
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        title = request.POST.get('title')
        description = request.POST.get('description')
        colab_url = request.POST.get('colab_url')
        difficulty = request.POST.get('difficulty')
        estimated_time = request.POST.get('estimated_time')
        keywords = request.POST.get('keywords')
        is_visible = True if request.POST.get('is_visible') == 'on' else False
        
        if not (subject_id and title and description and colab_url):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return redirect('staff_add_colab_notebook')
        
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            
            # Vérifier que le sujet appartient bien au professeur
            if subject.staff != staff:
                messages.error(request, "Vous n'êtes pas autorisé à ajouter des exercices pour ce module")
                return redirect('staff_add_colab_notebook')
            
            # Créer le notebook
            notebook = GoogleColabNotebook(
                subject=subject,
                title=title,
                description=description,
                colab_url=colab_url,
                difficulty=difficulty,
                created_by=staff,
                is_visible=is_visible,
                estimated_time=estimated_time or 60,
                keywords=keywords
            )
            notebook.save()
            
            messages.success(request, "Exercice Google Colab ajouté avec succès")
            return redirect('staff_colab_notebooks')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout de l'exercice : {str(e)}")
    
    context = {
        'subjects': subjects,
        'page_title': 'Ajouter un Exercice Google Colab'
    }
    return render(request, 'staff_template/staff_add_colab_notebook.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_edit_colab_notebook(request, notebook_id):
    """Vue pour modifier un notebook Google Colab existant."""
    staff = get_object_or_404(Staff, admin=request.user)
    notebook = get_object_or_404(GoogleColabNotebook, id=notebook_id, created_by=staff)
    subjects = Subject.objects.filter(staff=staff)
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        title = request.POST.get('title')
        description = request.POST.get('description')
        colab_url = request.POST.get('colab_url')
        difficulty = request.POST.get('difficulty')
        estimated_time = request.POST.get('estimated_time')
        keywords = request.POST.get('keywords')
        is_visible = True if request.POST.get('is_visible') == 'on' else False
        
        if not (subject_id and title and description and colab_url):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return redirect('staff_edit_colab_notebook', notebook_id=notebook.id)
        
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            
            # Vérifier que le sujet appartient bien au professeur
            if subject.staff != staff:
                messages.error(request, "Vous n'êtes pas autorisé à modifier cet exercice")
                return redirect('staff_colab_notebooks')
            
            # Mettre à jour le notebook
            notebook.subject = subject
            notebook.title = title
            notebook.description = description
            notebook.colab_url = colab_url
            notebook.difficulty = difficulty
            notebook.is_visible = is_visible
            notebook.estimated_time = estimated_time or 60
            notebook.keywords = keywords
            notebook.save()
            
            messages.success(request, "Exercice Google Colab modifié avec succès")
            return redirect('staff_colab_notebooks')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification de l'exercice : {str(e)}")
    
    context = {
        'notebook': notebook,
        'subjects': subjects,
        'page_title': 'Modifier un Exercice Google Colab'
    }
    return render(request, 'staff_template/staff_edit_colab_notebook.html', context)

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_delete_colab_notebook(request, notebook_id):
    """Vue pour supprimer un notebook Google Colab."""
    staff = get_object_or_404(Staff, admin=request.user)
    notebook = get_object_or_404(GoogleColabNotebook, id=notebook_id, created_by=staff)
    
    try:
        notebook.delete()
        messages.success(request, "Exercice Google Colab supprimé avec succès")
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression : {str(e)}")
    
    return redirect('staff_colab_notebooks')

@login_required(login_url='login')
@user_passes_test(is_staff)
def staff_view_student_progress(request, notebook_id):
    """Vue pour voir la progression des étudiants sur un notebook spécifique."""
    staff = get_object_or_404(Staff, admin=request.user)
    notebook = get_object_or_404(GoogleColabNotebook, id=notebook_id, created_by=staff)
    
    # Récupérer les étudiants de la filière correspondant au module
    students = Student.objects.filter(course=staff.course)
    total_students = students.count()
    
    # Récupérer les progressions pour ce notebook
    progresses = ColabNotebookProgress.objects.filter(
        notebook=notebook,
        student__in=students
    )
    
    # Calculer les statistiques
    completed_count = progresses.filter(is_completed=True).count()
    in_progress_count = progresses.filter(is_completed=False, progress_percent__gt=0).count()
    not_started_count = total_students - completed_count - in_progress_count
    
    # Calculer les pourcentages
    completed_percent = (completed_count / total_students * 100) if total_students > 0 else 0
    in_progress_percent = (in_progress_count / total_students * 100) if total_students > 0 else 0
    not_started_percent = (not_started_count / total_students * 100) if total_students > 0 else 0
    
    # Créer un dictionnaire pour associer chaque étudiant à sa progression
    student_progresses = {}
    for student in students:
        progress = progresses.filter(student=student).first()
        if not progress:
            # Si pas de progression enregistrée, créer un objet vide
            student_progresses[student] = {
                'progress_percent': 0,
                'is_completed': False,
                'last_accessed': None,
                'completed_date': None,
                'notes': '',
                'personal_colab_url': '',
                'score': None,
                'feedback': ''
            }
        else:
            student_progresses[student] = {
                'progress_percent': progress.progress_percent,
                'is_completed': progress.is_completed,
                'last_accessed': progress.last_accessed,
                'completed_date': progress.completed_date,
                'notes': progress.notes,
                'personal_colab_url': progress.personal_colab_url,
                'score': progress.score,
                'feedback': progress.feedback
            }
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        score = request.POST.get('score')
        feedback = request.POST.get('feedback')
        
        try:
            student = get_object_or_404(Student, id=student_id)
            progress = ColabNotebookProgress.objects.get(notebook=notebook, student=student)
            
            if score:
                try:
                    score = float(score)
                    if 0 <= score <= 20:  # Vérifier que la note est entre 0 et 20
                        progress.score = score
                    else:
                        messages.error(request, "La note doit être comprise entre 0 et 20")
                        return redirect('staff_view_student_progress', notebook_id=notebook.id)
                except ValueError:
                    messages.error(request, "La note doit être un nombre")
                    return redirect('staff_view_student_progress', notebook_id=notebook.id)
            
            progress.feedback = feedback
            progress.save()
            
            messages.success(request, "Note et commentaires enregistrés avec succès")
            return redirect('staff_view_student_progress', notebook_id=notebook.id)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'enregistrement : {str(e)}")
    
    context = {
        'notebook': notebook,
        'student_progresses': student_progresses,
        'stats': {
            'completed': {
                'count': completed_count,
                'percent': round(completed_percent, 1)
            },
            'in_progress': {
                'count': in_progress_count,
                'percent': round(in_progress_percent, 1)
            },
            'not_started': {
                'count': not_started_count,
                'percent': round(not_started_percent, 1)
            }
        },
        'page_title': f'Progression des étudiants - {notebook.title}'
    }
    return render(request, 'staff_template/staff_view_student_progress.html', context)
