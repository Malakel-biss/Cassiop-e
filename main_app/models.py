from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone




class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = CustomUser(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        assert extra_fields["is_staff"]
        assert extra_fields["is_superuser"]
        return self._create_user(email, password, **extra_fields)


class Session(models.Model):
    start_year = models.DateField()
    end_year = models.DateField()

    def __str__(self):
        return "From " + str(self.start_year) + " to " + str(self.end_year)


class CustomUser(AbstractUser):
    USER_TYPE = ((1, "HOD"), (2, "Staff"), (3, "Student"))
    GENDER = [("M", "Masculin"), ("F", "Féminin")]
    
    
    username = None  # Removed username, using email instead
    email = models.EmailField(unique=True)
    user_type = models.CharField(default=1, choices=USER_TYPE, max_length=1)
    gender = models.CharField(max_length=1, choices=GENDER)
    profile_pic = models.ImageField()
    address = models.TextField()
    fcm_token = models.TextField(default="")  # For firebase notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.last_name + ", " + self.first_name


class Admin(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

class Course(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)  # ✅ Add this
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name


class Student(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return self.admin.last_name + ", " + self.admin.first_name


class Staff(models.Model):
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.admin.last_name + " " + self.admin.first_name


class Subject(models.Model):
    name = models.CharField(max_length=120)
    staff = models.ForeignKey(Staff,on_delete=models.CASCADE,)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Module(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE,null=True)  # optional if tied to Course
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    name = models.CharField(max_length=200)
    pdf = models.FileField(upload_to="lessons/pdfs/", blank=True, null=True)
    video = models.FileField(upload_to="lessons/videos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.module.name})"


class Attendance(models.Model):
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING)
    subject = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AttendanceReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StudentResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    test = models.FloatField(default=0)
    exam = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CourseMaterial(models.Model):
    MATERIAL_TYPES = (
        ('pdf', 'Document PDF'),
        ('video', 'Vidéo'),
        ('exercise', 'Exercice'),
        ('other', 'Autre'),
    )
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES)
    file = models.FileField(upload_to='course_materials/')
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=True)
    estimated_time = models.IntegerField(default=30, help_text="Temps estimé en minutes")

    def __str__(self):
        return f"{self.title} - {self.subject.name}"

    class Meta:
        ordering = ['-upload_date']


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:
            Admin.objects.create(admin=instance)
        if instance.user_type == 2:
            Staff.objects.create(admin=instance)
        if instance.user_type == 3:
            Student.objects.create(admin=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 1:
        instance.admin.save()
    if instance.user_type == 2:
        instance.staff.save()
    if instance.user_type == 3:
        instance.student.save()


class Assignment(models.Model):
    ASSIGNMENT_TYPES = (
        ('quiz', 'Quiz'),
        ('homework', 'Devoir'),
    )
    
    QUIZ_TYPES = (
        ('qcm', 'QCM'),
        ('text', 'Question ouverte'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES)
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES, null=True, blank=True)
    support_file = models.FileField(upload_to='assignments/supports/', null=True, blank=True)
    total_points = models.IntegerField(default=20)

    def __str__(self):
        return f"{self.title} - {self.subject.name}"

class Question(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    points = models.IntegerField(default=1)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"Question {self.order} - {self.assignment.title}"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200, default='')
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} - {'Correct' if self.is_correct else 'Incorrect'}"

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    submission_file = models.FileField(upload_to='assignments/submissions/', null=True, blank=True)
    is_late = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.admin.first_name} - {self.assignment.title}"

    def save(self, *args, **kwargs):
        if self.assignment.due_date < timezone.now():
            self.is_late = True
        super().save(*args, **kwargs)

class QuizAnswer(models.Model):
    submission = models.ForeignKey(AssignmentSubmission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(null=True, blank=True)
    is_correct = models.BooleanField(null=True)

    def __str__(self):
        return f"Réponse de {self.submission.student.admin.first_name} pour {self.question.text}"

class StudentProgress(models.Model):
    STATUS_CHOICES = (
        ('not_started', 'Non commencé'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    progress_percent = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'subject')
        
    def __str__(self):
        return f"{self.student.admin.first_name} - {self.subject.name} ({self.get_status_display()})"

class MaterialProgress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    material = models.ForeignKey(CourseMaterial, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    time_spent = models.IntegerField(default=0, help_text="Temps passé en minutes")
    completed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('student', 'material')
        
    def __str__(self):
        status = "Complété" if self.is_completed else "En cours"
        return f"{self.student.admin.first_name} - {self.material.title} ({status})"

class GoogleColabNotebook(models.Model):
    """Modèle pour intégrer des exercices pratiques via Google Colab."""
    
    DIFFICULTY_CHOICES = (
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    )
    
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    description = models.TextField()
    colab_url = models.URLField(help_text="URL du notebook Google Colab")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    created_by = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='colab_notebooks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_visible = models.BooleanField(default=True)
    estimated_time = models.IntegerField(default=60, help_text="Temps estimé en minutes")
    keywords = models.CharField(max_length=255, blank=True, help_text="Mots-clés séparés par des virgules")
    
    def __str__(self):
        return f"{self.title} - {self.subject.name} ({self.get_difficulty_display()})"
    
    class Meta:
        ordering = ['-created_at']

class ColabNotebookProgress(models.Model):
    """Suivi de la progression d'un étudiant sur un notebook Colab."""
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    notebook = models.ForeignKey(GoogleColabNotebook, on_delete=models.CASCADE)
    personal_colab_url = models.URLField(blank=True, help_text="URL personnelle du notebook de l'étudiant")
    is_completed = models.BooleanField(default=False)
    progress_percent = models.FloatField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Notes personnelles de l'étudiant sur ce notebook")
    score = models.FloatField(null=True, blank=True, help_text="Note attribuée par le professeur")
    feedback = models.TextField(blank=True, help_text="Commentaires du professeur")
    
    class Meta:
        unique_together = ('student', 'notebook')
        
    def __str__(self):
        status = "Complété" if self.is_completed else "En cours"
        return f"{self.student.admin.first_name} - {self.notebook.title} ({status})"

class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    content = models.TextField()
    attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"De {self.sender.first_name} à {self.receiver.first_name}: {self.subject}"

class ForumCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Forum Categories"
    
    def __str__(self):
        course_name = self.course.name if self.course else "Général"
        return f"{self.name} ({course_name})"

class ForumTopic(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return self.title

class ForumReply(models.Model):
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_solution = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
        verbose_name_plural = "Forum Replies"
    
    def __str__(self):
        return f"Réponse de {self.created_by.first_name} sur {self.topic.title}"

class IoTDevice(models.Model):
    DEVICE_TYPES = (
        ('temperature', 'Capteur de température'),
        ('humidity', 'Capteur d\'humidité'),
        ('motion', 'Capteur de mouvement'),
        ('light', 'Capteur de luminosité'),
        ('cpu', 'Utilisation CPU'),
        ('memory', 'Utilisation mémoire'),
        ('disk', 'Utilisation disque'),
        ('network', 'Trafic réseau'),
        ('other', 'Autre'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('maintenance', 'En maintenance'),
    )
    
    name = models.CharField(max_length=100)
    device_id = models.CharField(max_length=50, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='iot_devices')
    created_by = models.ForeignKey(Staff, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_data_received = models.DateTimeField(null=True, blank=True)
    
    # Nouveaux champs pour la pédagogie
    learning_objective = models.TextField(
        help_text="Objectif pédagogique de l'utilisation de cet appareil",
        default="Analyse des données en temps réel pour comprendre les concepts fondamentaux"
    )
    expected_outcomes = models.TextField(
        help_text="Résultats attendus de l'analyse des données",
        default="Compréhension des patterns de données et capacité à interpréter les résultats"
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=(
            ('beginner', 'Débutant'),
            ('intermediate', 'Intermédiaire'),
            ('advanced', 'Avancé'),
        ),
        default='intermediate'
    )
    
    def __str__(self):
        return f"{self.name} ({self.get_device_type_display()})"
    
    class Meta:
        ordering = ['-created_at']

class IoTData(models.Model):
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='data_points')
    timestamp = models.DateTimeField(auto_now_add=True)
    value = models.FloatField()
    unit = models.CharField(max_length=20, default='')
    metadata = models.JSONField(default=dict, help_text="Données additionnelles (ex: CPU%, RAM%, etc.)")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'timestamp']),
        ]

class IoTAnalysis(models.Model):
    ANALYSIS_TYPES = (
        ('statistical', 'Analyse statistique'),
        ('anomaly', 'Détection d\'anomalies'),
        ('trend', 'Analyse de tendances'),
        ('prediction', 'Prédiction'),
        ('clustering', 'Clustering'),
        ('correlation', 'Analyse de corrélation'),
    )
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='analyses')
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    parameters = models.JSONField(default=dict, help_text="Paramètres utilisés pour l'analyse")
    results = models.JSONField(default=dict, help_text="Résultats de l'analyse")
    created_by = models.ForeignKey(Staff, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Nouveaux champs pour la pédagogie
    learning_points = models.TextField(
        help_text="Points clés à retenir de cette analyse",
        default="Analyse des tendances et identification des patterns"
    )
    interpretation_guide = models.TextField(
        help_text="Guide d'interprétation des résultats",
        default="Guide d'interprétation des données et des résultats d'analyse"
    )
    suggested_exercises = models.TextField(
        help_text="Exercices suggérés basés sur cette analyse",
        default="Exercices pratiques pour approfondir la compréhension"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "IoT Analyses"

class IoTAssignment(models.Model):
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    learning_objectives = models.TextField(help_text="Objectifs d'apprentissage de ce travail")
    instructions = models.TextField(
        help_text="Instructions détaillées pour l'étudiant",
        default="Veuillez analyser les données fournies et rédiger un rapport."
    )
    due_date = models.DateTimeField()
    points = models.IntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Staff, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    # Nouveaux champs pour la pédagogie
    difficulty_level = models.CharField(max_length=20, choices=(
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    ), default='intermediate')
    required_skills = models.TextField(help_text="Compétences requises pour ce travail")
    evaluation_criteria = models.TextField(
        help_text="Critères d'évaluation",
        default="Analyse de la qualité des résultats, clarté de l'interprétation, respect des consignes"
    )
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.device.name}"

class IoTAssignmentSubmission(models.Model):
    assignment = models.ForeignKey(IoTAssignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    analysis = models.TextField(help_text="Analyse des données réalisée par l'étudiant")
    conclusion = models.TextField(help_text="Conclusion et interprétation des résultats")
    files = models.FileField(upload_to='iot_submissions/', blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    is_graded = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student']

    def __str__(self):
        return f"{self.student.admin.get_full_name()} - {self.assignment.title}"
