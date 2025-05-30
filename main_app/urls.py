"""student_management_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from main_app.EditResultView import EditResultView

from . import hod_views, staff_views, student_views, views

urlpatterns = [
    path("", views.login_page, name='login_page'),
    path("get_attendance", views.get_attendance, name='get_attendance'),
    path("firebase-messaging-sw.js", views.showFirebaseJS, name='showFirebaseJS'),
    path("doLogin/", views.doLogin, name='user_login'),
    path("logout_user/", views.logout_user, name='user_logout'),
    path("admin/home/", hod_views.admin_home, name='admin_home'),
    path("staff/add", hod_views.add_staff, name='add_staff'),
    path("course/add", hod_views.add_course, name='add_course'),
    path("send_student_notification/", hod_views.send_student_notification,
         name='send_student_notification'),
    path("send_staff_notification/", hod_views.send_staff_notification,
         name='send_staff_notification'),
    path("add_session/", hod_views.add_session, name='add_session'),
    path("admin_notify_student", hod_views.admin_notify_student,
         name='admin_notify_student'),
    path("admin_notify_staff", hod_views.admin_notify_staff,
         name='admin_notify_staff'),
    path("admin_view_profile", hod_views.admin_view_profile,
         name='admin_view_profile'),
    path("check_email_availability", hod_views.check_email_availability,
         name="check_email_availability"),
    path("session/manage/", hod_views.manage_session, name='manage_session'),
    path("session/edit/<int:session_id>",
         hod_views.edit_session, name='edit_session'),
    path("student/view/feedback/", hod_views.student_feedback_message,
         name="student_feedback_message",),
    path("staff/view/feedback/", hod_views.staff_feedback_message,
         name="staff_feedback_message",),
    path("student/view/leave/", hod_views.view_student_leave,
         name="view_student_leave",),
    path("staff/view/leave/", hod_views.view_staff_leave, name="view_staff_leave",),
    path("attendance/view/", hod_views.admin_view_attendance,
         name="admin_view_attendance",),
    path("attendance/fetch/", hod_views.get_admin_attendance,
         name='get_admin_attendance'),
    path("student/add/", hod_views.add_student, name='add_student'),
    path("subject/add/", hod_views.add_subject, name='add_subject'),
    path("staff/manage/", hod_views.manage_staff, name='manage_staff'),
    path("student/manage/", hod_views.manage_student, name='manage_student'),
    path("course/manage/", hod_views.manage_course, name='manage_course'),
    path("subject/manage/", hod_views.manage_subject, name='manage_subject'),
    path("staff/edit/<int:staff_id>", hod_views.edit_staff, name='edit_staff'),
    path("staff/delete/<int:staff_id>",
         hod_views.delete_staff, name='delete_staff'),

    path("course/delete/<int:course_id>",
         hod_views.delete_course, name='delete_course'),

    path("subject/delete/<int:subject_id>",
         hod_views.delete_subject, name='delete_subject'),

    path("session/delete/<int:session_id>",
         hod_views.delete_session, name='delete_session'),

    path("student/delete/<int:student_id>",
         hod_views.delete_student, name='delete_student'),
    path("student/edit/<int:student_id>",
         hod_views.edit_student, name='edit_student'),
    path("course/edit/<int:course_id>",
         hod_views.edit_course, name='edit_course'),
    path("subject/edit/<int:subject_id>",
         hod_views.edit_subject, name='edit_subject'),


    # Staff
    path("staff/home/", staff_views.staff_home, name='staff_home'),
    path("staff/apply/leave/", staff_views.staff_apply_leave,
         name='staff_apply_leave'),
    path("staff/feedback/", staff_views.staff_feedback, name='staff_feedback'),
    path("staff/view/profile/", staff_views.staff_view_profile,
         name='staff_view_profile'),
    path("staff/attendance/take/", staff_views.staff_take_attendance,
         name='staff_take_attendance'),
    path("staff/attendance/update/", staff_views.staff_update_attendance,
         name='staff_update_attendance'),
    path("staff/get_students/", staff_views.get_students, name='get_students'),
    path("staff/attendance/fetch/", staff_views.get_student_attendance,
         name='get_student_attendance'),
    path("staff/attendance/save/",
         staff_views.save_attendance, name='save_attendance'),
    path("staff/attendance/update/",
         staff_views.update_attendance, name='update_attendance'),
    path("staff/fcmtoken/", staff_views.staff_fcmtoken, name='staff_fcmtoken'),
    path("staff/view/notification/", staff_views.staff_view_notification,
         name="staff_view_notification"),
    path("staff/result/add/", staff_views.staff_add_result, name='staff_add_result'),
    path("staff/result/edit/", EditResultView.as_view(),
         name='edit_student_result'),
    path('staff/result/fetch/', staff_views.fetch_student_result,
         name='fetch_student_result'),
    path('staff/course-materials/', staff_views.staff_course_materials, name='staff_course_materials'),
    path('staff/course-materials/add/', staff_views.staff_add_course_material, name='staff_add_course_material'),
    path('staff/course-materials/edit/<int:material_id>/', staff_views.staff_edit_course_material, name='staff_edit_course_material'),
    path('staff/course-materials/delete/<int:material_id>/', staff_views.staff_delete_course_material, name='staff_delete_course_material'),
    path('staff/assignments/', staff_views.staff_assignments, name='staff_assignments'),
    path('staff/add_assignment/', staff_views.staff_add_assignment, name='staff_add_assignment'),
    path('staff/view_submissions/<int:assignment_id>/', staff_views.staff_view_submissions, name='staff_view_submissions'),
    path('staff/grade_submission/<int:submission_id>/', staff_views.staff_grade_submission, name='staff_grade_submission'),
    path('toggle_assignment_status/<int:assignment_id>/', staff_views.toggle_assignment_status, name='toggle_assignment_status'),

    # STAFF GOOGLE COLAB URLS
    path('staff/colab-notebooks/', staff_views.staff_colab_notebooks, name='staff_colab_notebooks'),
    path('staff/add-colab-notebook/', staff_views.staff_add_colab_notebook, name='staff_add_colab_notebook'),
    path('staff/edit-colab-notebook/<int:notebook_id>/', staff_views.staff_edit_colab_notebook, name='staff_edit_colab_notebook'),
    path('staff/delete-colab-notebook/<int:notebook_id>/', staff_views.staff_delete_colab_notebook, name='staff_delete_colab_notebook'),
    path('staff/view-student-progress/<int:notebook_id>/', staff_views.staff_view_student_progress, name='staff_view_student_progress'),

    # STUDENT MESSAGING URLS
    path('student/inbox/', student_views.student_inbox, name="student_inbox"),
    path('student/sent_messages/', student_views.student_sent_messages, name="student_sent_messages"),
    path('student/compose_message/', student_views.student_compose_message, name="student_compose_message"),
    path('student/view_message/<int:message_id>/', student_views.student_view_message, name="student_view_message"),

    # STUDENT FORUM URLS
    path('student/forum/', student_views.student_forum_categories, name="student_forum_categories"),
    path('student/forum/category/<int:category_id>/', student_views.student_forum_topics, name="student_forum_topics"),
    path('student/forum/topic/<int:topic_id>/', student_views.student_forum_topic_detail, name="student_forum_topic_detail"),
    path('student/forum/category/<int:category_id>/new_topic/', student_views.student_create_topic, name="student_create_topic"),

    # STUDENT GOOGLE COLAB URLS
    path('student/colab-notebooks/', student_views.student_colab_notebooks, name='student_colab_notebooks'),
    path('student/view-colab-notebook/<int:notebook_id>/', student_views.student_view_colab_notebook, name='student_view_colab_notebook'),
    path('student/update-colab-progress/<int:notebook_id>/', student_views.student_update_colab_progress, name='student_update_colab_progress'),

    # STAFF MESSAGING URLS
    path('staff/inbox/', staff_views.staff_inbox, name="staff_inbox"),
    path('staff/sent_messages/', staff_views.staff_sent_messages, name="staff_sent_messages"),
    path('staff/compose_message/', staff_views.staff_compose_message, name="staff_compose_message"),
    path('staff/view_message/<int:message_id>/', staff_views.staff_view_message, name="staff_view_message"),

    # STAFF FORUM URLS
    path('staff/forum/', staff_views.staff_forum_categories, name="staff_forum_categories"),
    path('staff/forum/category/<int:category_id>/', staff_views.staff_forum_topics, name="staff_forum_topics"),
    path('staff/forum/topic/<int:topic_id>/', staff_views.staff_forum_topic_detail, name="staff_forum_topic_detail"),
    path('staff/forum/category/<int:category_id>/new_topic/', staff_views.staff_create_topic, name="staff_create_topic"),
    path('staff/forum/manage_categories/', staff_views.staff_manage_forum_category, name="staff_manage_forum_category"),

    # Student
    path("student/home/", student_views.student_home, name='student_home'),
    path("student/view/attendance/", student_views.student_view_attendance,
         name='student_view_attendance'),
    path("student/apply/leave/", student_views.student_apply_leave,
         name='student_apply_leave'),
    path("student/feedback/", student_views.student_feedback,
         name='student_feedback'),
    path("student/view/profile/", student_views.student_view_profile,
         name='student_view_profile'),
    path("student/fcmtoken/", student_views.student_fcmtoken,
         name='student_fcmtoken'),
    path("student/view/notification/", student_views.student_view_notification,
         name="student_view_notification"),
    path('student/view/result/', student_views.student_view_result,
         name='student_view_result'),
    path('student/course-materials/', student_views.student_course_materials, name='student_course_materials'),
    path('student/assignments/', student_views.student_assignments, name='student_assignments'),
    path('student/view_assignment/<int:assignment_id>/', student_views.student_view_assignment, name='student_view_assignment'),
    path('student/view_submission/<int:submission_id>/', student_views.student_view_submission, name='student_view_submission'),

    # URLs pour les appareils IoT (Staff)
    path('staff/iot-devices/', views.staff_iot_devices, name='staff_iot_devices'),
    path('staff/iot-devices/<int:device_id>/', views.staff_iot_device_detail, name='staff_iot_device_detail'),
    path('staff/iot-devices/<int:device_id>/analysis/', views.staff_iot_analysis, name='staff_iot_analysis'),
    path('staff/iot-devices/simulate-cpu/', views.simulate_cpu_temperature, name='simulate_cpu_temperature'),
    path('staff/iot-devices/simulate-system/', views.simulate_system_sensor, name='simulate_system_sensor'),
    
    # URLs pour les appareils IoT (Students)
    path('student/iot-devices/', views.student_iot_devices, name='student_iot_devices'),
    path('student/iot-devices/<int:device_id>/', views.student_iot_device_detail, name='student_iot_device_detail'),
    
    # API endpoints pour les données IoT
    path('api/iot-data/', views.api_iot_data, name='api_iot_data'),
    path('api/iot-device/<int:device_id>/data/', views.api_iot_device_data, name='api_iot_device_data'),
]
