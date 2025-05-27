from django.core.management.base import BaseCommand
from main_app.models import Staff, Subject, Course, CustomUser

class Command(BaseCommand):
    help = 'Crée un professeur et une matière GL pour les capteurs IoT'

    def handle(self, *args, **kwargs):
        # Créer un cours
        course, created = Course.objects.get_or_create(
            name='Informatique',
            defaults={'description': "Cours d'informatique générale"}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Cours créé: {course.name}'))

        # Créer un utilisateur professeur (CustomUser)
        user, created = CustomUser.objects.get_or_create(
            email='professeur1@example.com',
            defaults={
                'first_name': 'Jean',
                'last_name': 'Dupont',
                'user_type': '2',  # 2 = Staff
                'gender': 'M',
                'address': "123 Rue de l'École",
                'is_staff': True
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Utilisateur créé: {user.email}'))
        else:
            self.stdout.write(self.style.WARNING(f'Utilisateur déjà existant: {user.email}'))

        # Créer un professeur
        staff, created = Staff.objects.get_or_create(
            admin=user,
            defaults={
                'course': course
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Professeur créé: {staff.admin.get_full_name()}'))
        else:
            self.stdout.write(self.style.WARNING(f'Professeur déjà existant: {staff.admin.get_full_name()}'))

        # Créer une matière GL en liant le staff
        subject, created = Subject.objects.get_or_create(
            name='GL',
            course=course,
            staff=staff
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Matière créée: {subject.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Matière déjà existante: {subject.name}'))

        self.stdout.write(self.style.SUCCESS('Données initiales créées avec succès!')) 