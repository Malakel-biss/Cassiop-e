# 🎓 Cassiopée - Application SAAS d'enseignement et de prototypage basée sur l'IA générative

![Cassiop-e Logo](static/images/logo.png)

## 📋 Table des Matières
- [À Propos](#-à-propos)
- [Fonctionnalités](#-fonctionnalités)
  - [Administrateur](#-administrateur)
  - [Professeur](#-professeur)
  - [Étudiant](#-étudiant)
- [Captures d'Écran](#-captures-décran)
  - [Interface Administrateur](#-interface-administrateur)
  - [Interface Professeur](#-interface-professeur)
  - [Interface Étudiant](#-interface-étudiant)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Documentation API](#-documentation-api)
- [Contribution](#-contribution)
- [Licence](#-licence)

## 🎯 À Propos

Cassiop-e est une plateforme éducative innovante qui combine l'apprentissage traditionnel avec les technologies modernes. Notre solution SAAS intègre l'IA générative pour offrir une expérience d'apprentissage personnalisée et interactive, tout en facilitant la gestion administrative des établissements d'enseignement.

### Objectifs
- Moderniser l'enseignement avec des outils numériques avancés
- Faciliter la gestion administrative des établissements
- Offrir un environnement d'apprentissage interactif et collaboratif
- Intégrer l'IA pour personnaliser l'expérience d'apprentissage
- Permettre le prototypage et l'expérimentation avec l'IoT

## ✨ Fonctionnalités

### 👨‍💼 Administrateur
- 🏫 Gestion complète des filières
  - Création et modification des filières
  - Gestion des matières par filière
  - Attribution des professeurs
- 👥 Gestion des utilisateurs
  - Création et gestion des comptes professeurs
  - Gestion des inscriptions étudiants
  - Attribution des rôles et permissions
- 📊 Tableaux de bord analytiques
  - Statistiques de présence
  - Performances des étudiants
  - Activité des professeurs
- ⚙️ Configuration système
  - Paramètres de la plateforme
  - Gestion des sessions
  - Configuration des notifications

### 👨‍🏫 Professeur
- 📚 Gestion des cours
  - Création de contenu pédagogique
  - Gestion des matières assignées
  - Planification des cours
- 📝 Évaluation
  - Création de quiz avec notation automatique
  - Gestion des devoirs
  - Suivi des notes
- 📊 Suivi des étudiants
  - Suivi de la progression
  - Gestion des présences
  - Analyse des performances
- 💻 Outils pédagogiques
  - Intégration Google Colab
  - Gestion des capteurs IoT
  - Création de ressources interactives
- 📱 Communication
  - Messagerie avec étudiants
  - Forum de discussion
  - Annonces de cours
- 📅 Gestion administrative
  - Demandes de congé
  - Planning des cours
  - Rapports d'activité

### 👨‍🎓 Étudiant
- 📚 Apprentissage
  - Accès aux cours et ressources
  - Participation aux quiz
  - Soumission des devoirs
- 💻 Outils interactifs
  - Notebooks Google Colab
  - Expérimentation IoT
  - Exercices pratiques
- 📊 Suivi personnel
  - Notes et progression
  - Historique des présences
  - Statistiques de performance
- 📱 Communication
  - Messagerie avec professeurs
  - Forum de discussion
  - Notifications en temps réel
- 📅 Gestion administrative
  - Demandes de congé
  - Emploi du temps
  - Documents administratifs

## 🖼️ Captures d'Écran

### Interface Administrateur
![Dashboard Administrateur](image/dashbadmin.png)
*Tableau de bord administrateur avec vue d'ensemble*

![Gestion des Modules](image/1admin.png)
*Interface de gestion des modules*

![Gestion des Professeurs](image/2admin.png)
*Gestion des professeurs*

### Interface Professeur
![Dashboard Professeur](image/homepageprof.png)
*Tableau de bord professeur*

![Google Colab](image/googlecolabsectionprof.png)
*Google Colab*

![Section IOT](image/sectioniotprof.png)
*Section IOT*

### Interface Étudiant
![Dashboard Étudiant](image/homepagestudent.png)
*Tableau de bord étudiant*

![Cours et Ressources](image/supportcoursetudiant)
*Accès aux cours et ressources*

![Quiz et Devoirs](image/devoirquizzetudiant.png)
*Interface des quiz et devoirs*

![Google Colab Section](image/googlecolabstudent.png)
*Google Colab Section*


## 🚀 Installation

### Prérequis
- Python 3.8+
- PostgreSQL 12+
- Node.js 14+ (pour les assets frontend)
- Git

### Installation des Dépendances

1. Cloner le repository :
```bash
git clone https://github.com/malakel-biss/Cassiop-e.git
cd Cassiop-e
```

2. Créer un environnement virtuel :
```bash
python -m venv env
source env/bin/activate  # Linux/Mac
# ou
.\env\Scripts\activate  # Windows
```

3. Installer les dépendances Python :
```bash
pip install -r requirements.txt
```

4. Installer les dépendances frontend :
```bash
npm install
```

### Configuration de la Base de Données

1. Créer une base de données PostgreSQL :
```sql
CREATE DATABASE cassiop_e;
```

2. Configurer les variables d'environnement :
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

3. Appliquer les migrations :
```bash
python manage.py migrate
```

4. Créer un superutilisateur :
```bash
python manage.py createsuperuser
```

## ⚙️ Configuration

### Variables d'Environnement
```env
DEBUG=True
SECRET_KEY=votre-clé-secrète
DATABASE_URL=postgresql://user:password@localhost:5432/cassiop_e
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Configuration des Capteurs IoT
1. Ajouter un nouveau capteur :
```bash
python manage.py create_computer_sensors
```

2. Configurer les paramètres du capteur dans l'interface d'administration

## 💻 Utilisation

### Démarrage du Serveur
```bash
python manage.py runserver
```

### Accès à l'Application
- Interface web : http://localhost:8000
- Interface d'administration : http://localhost:8000/admin

### Commandes Utiles
```bash
# Créer des données initiales
python manage.py create_initial_data

# Créer des capteurs de test
python manage.py create_computer_sensors

# Collecter les fichiers statiques
python manage.py collectstatic
```

## 🔌 Capteurs IoT

### Types de Capteurs Supportés
- CPU (Utilisation, température, fréquence)
- Mémoire (Utilisation RAM, swap)
- Disque (Espace, vitesse de lecture/écriture)
- Réseau (Bande passante, paquets)

### Ajout d'un Nouveau Capteur
1. Accéder à l'interface d'administration
2. Naviguer vers "IoT Devices"
3. Cliquer sur "Ajouter un capteur"
4. Remplir les informations requises
5. Sauvegarder

### Visualisation des Données
- Graphiques en temps réel
- Historique des mesures
- Export des données
- Analyse des tendances

## 📚 API Documentation

### Endpoints Principaux
```python
# Données des capteurs
GET /api/iot-data/
POST /api/iot-data/

# Gestion des capteurs
GET /api/iot-devices/
POST /api/iot-devices/

# Analyse des données
GET /api/iot-analysis/
```

### Authentification
```python
# Headers requis
{
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
}
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

### Standards de Code
- PEP 8 pour Python
- ESLint pour JavaScript
- Tests unitaires requis
- Documentation à jour

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.


<div align="center">
  <p>Made with ❤️ by l'équipe Cassiop-e</p>
  <p>© 2024 Cassiop-e. Tous droits réservés.</p>
</div>
