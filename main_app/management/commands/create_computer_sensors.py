from django.core.management.base import BaseCommand
from django.utils import timezone
from main_app.models import IoTDevice, IoTData, Subject, Staff
import random
import uuid
from datetime import timedelta

class Command(BaseCommand):
    help = 'Crée des capteurs d\'ordinateur et leurs données'

    def handle(self, *args, **kwargs):
        # Récupérer un professeur et une matière
        staff = Staff.objects.first()
        subject = Subject.objects.filter(name__icontains='informatique').first()
        
        if not staff or not subject:
            self.stdout.write(self.style.ERROR('Professeur ou matière non trouvés'))
            return

        # Créer les capteurs
        sensors = [
            {
                'name': 'Capteur CPU',
                'device_type': 'cpu',
                'description': 'Capteur de performance CPU',
                'location': 'Salle informatique',
                'learning_objective': 'Comprendre l\'utilisation du CPU et son impact sur les performances',
                'expected_outcomes': 'Analyse des pics d\'utilisation CPU et identification des processus gourmands',
                'difficulty_level': 'intermediate'
            },
            {
                'name': 'Capteur Mémoire',
                'device_type': 'memory',
                'description': 'Capteur d\'utilisation de la mémoire RAM',
                'location': 'Salle informatique',
                'learning_objective': 'Analyser l\'utilisation de la mémoire et la gestion de la RAM',
                'expected_outcomes': 'Comprendre les fuites de mémoire et l\'optimisation de la RAM',
                'difficulty_level': 'intermediate'
            },
            {
                'name': 'Capteur Disque',
                'device_type': 'disk',
                'description': 'Capteur d\'activité disque',
                'location': 'Salle informatique',
                'learning_objective': 'Étudier les performances du stockage',
                'expected_outcomes': 'Analyse des temps de lecture/écriture et optimisation du stockage',
                'difficulty_level': 'beginner'
            },
            {
                'name': 'Capteur Réseau',
                'device_type': 'network',
                'description': 'Capteur de trafic réseau',
                'location': 'Salle informatique',
                'learning_objective': 'Comprendre le trafic réseau et la bande passante',
                'expected_outcomes': 'Analyse du trafic réseau et identification des applications gourmandes',
                'difficulty_level': 'advanced'
            }
        ]

        created_devices = []
        for sensor_data in sensors:
            device_id = f"DEVICE_{uuid.uuid4().hex[:8].upper()}"
            device = IoTDevice.objects.create(
                device_id=device_id,
                created_by=staff,
                subject=subject,
                **sensor_data
            )
            created_devices.append(device)
            self.stdout.write(self.style.SUCCESS(f'Capteur créé: {device.name}'))

        # Générer des données pour chaque capteur
        now = timezone.now()
        for device in created_devices:
            # Générer 24 heures de données (une mesure par heure)
            for hours_ago in range(24):
                timestamp = now - timedelta(hours=hours_ago)
                
                if device.device_type == 'cpu':
                    value = random.uniform(10, 90)  # Pourcentage d'utilisation CPU
                    metadata = {
                        'cores': 4,
                        'temperature': random.uniform(40, 80),
                        'frequency': random.uniform(2.0, 3.5)
                    }
                elif device.device_type == 'memory':
                    value = random.uniform(30, 85)  # Pourcentage d'utilisation mémoire
                    metadata = {
                        'total': 8192,  # MB
                        'used': int(8192 * value / 100),
                        'available': int(8192 * (100 - value) / 100)
                    }
                elif device.device_type == 'disk':
                    value = random.uniform(20, 95)  # Pourcentage d'utilisation disque
                    metadata = {
                        'total': 512000,  # MB
                        'used': int(512000 * value / 100),
                        'read_speed': random.uniform(50, 200),
                        'write_speed': random.uniform(30, 150)
                    }
                else:  # network
                    value = random.uniform(1, 100)  # Mbps
                    metadata = {
                        'upload': random.uniform(0.5, 50),
                        'download': random.uniform(1, 100),
                        'packets_sent': random.randint(1000, 10000),
                        'packets_received': random.randint(1000, 10000)
                    }

                IoTData.objects.create(
                    device=device,
                    timestamp=timestamp,
                    value=value,
                    unit='%' if device.device_type != 'network' else 'Mbps',
                    metadata=metadata
                )

            self.stdout.write(self.style.SUCCESS(f'Données générées pour {device.name}'))

        self.stdout.write(self.style.SUCCESS('Tous les capteurs et données ont été créés avec succès!')) 