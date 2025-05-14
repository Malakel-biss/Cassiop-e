import json

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test

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
        'page_title': 'Staff Panel - ' + str(staff.admin.last_name) + ' (' + str(staff.course) + ')',
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
        'page_title': 'Take Attendance'
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
        'page_title': 'Update Attendance'
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
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_apply_leave.html", context)


def staff_feedback(request):
    form = FeedbackStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStaff.objects.filter(staff=staff),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('staff_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_feedback.html", context)


def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    form = StaffEditForm(request.POST or None, request.FILES or None,instance=staff)
    context = {'form': form, 'page_title': 'View/Update Profile'}
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
                messages.success(request, "Profile Updated!")
                return redirect(reverse('staff_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "staff_template/staff_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
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
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)


def staff_add_result(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    sessions = Session.objects.all()
    context = {
        'page_title': 'Result Upload',
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
                messages.success(request, "Scores Updated")
            except:
                result = StudentResult(student=student, subject=subject, test=test, exam=exam)
                result.save()
                messages.success(request, "Scores Saved")
        except Exception as e:
            messages.warning(request, "Error Occured While Processing Form")
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
