#!/usr/bin/env python
"""
Script pour générer une base de données SQLite de démonstration pour ChronoTrak
avec des données fictives réalistes.

Usage:
  python generate_demo_db.py [--output DB_PATH]

Options:
  --output DB_PATH    Chemin du fichier de base de données à créer (par défaut: instance/chronotrak.db)
"""

import os
import sys
import random
import argparse
from datetime import datetime, timedelta
import time
from flask import current_app
from werkzeug.security import generate_password_hash

# Configuration du chemin d'accès
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)  # Remonter d'un niveau si nécessaire

# Ajouter le répertoire au chemin Python
sys.path.insert(0, root_dir)

# Importer les modules après avoir configuré les chemins
try:
    from app import create_app, db, bcrypt
    from app.models.user import User
    from app.models.client import Client
    from app.models.project import Project, CreditLog
    from app.models.task import Task, TimeEntry, Comment
    from app.models.notification import NotificationPreference
    from app.utils import get_utc_now
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    print(f"Vérifiez que les fichiers de l'application sont corrects.")
    print(f"Chemin racine actuel: {root_dir}")
    sys.exit(1)

# Listes de données fictives pour la génération
FIRST_NAMES = ["Marie", "Jean", "Sophie", "Thomas", "Julie", "Pierre", "Léa", "Nicolas", 
               "Émilie", "Lucas", "Camille", "Antoine", "Laura", "Alexandre", "Emma", "David"]

LAST_NAMES = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", 
              "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David"]

COMPANY_NAMES = [
    "TechSolutions", "InfoSys", "DataCorp", "WebDesign Plus", "CloudServices", 
    "SoftDev", "Innovatech", "Numérique Express", "Cyber Sécurité", "IT Conseil",
    "e-Commerce Pro", "Digital Marketing", "AppFactory", "Smart Solutions", "TechNet",
]

COMPANY_TYPES = ["SARL", "SAS", "SA", "EURL", "SNC", "SASU"]

EMAIL_DOMAINS = ["gmail.com", "outlook.fr", "yahoo.fr", "orange.fr", "free.fr", "entreprise.com"]

STREET_NAMES = ["rue de la Paix", "avenue des Champs-Élysées", "boulevard Saint-Michel", 
                "rue du Commerce", "avenue Victor Hugo", "rue de Rivoli", "place de la République"]

CITIES = ["Paris", "Lyon", "Marseille", "Bordeaux", "Lille", "Nantes", "Strasbourg", 
          "Toulouse", "Nice", "Rennes", "Montpellier", "Orléans"]

POSTAL_CODES = ["75001", "69001", "13001", "33000", "59000", "44000", "67000", 
                "31000", "06000", "35000", "34000", "45000"]

PROJECT_NAMES = [
    "Refonte du site web", "Application mobile", "Migration cloud", "Audit de sécurité", 
    "Intégration CRM", "Automatisation ERP", "Déploiement BI", "Maintenance annuelle", 
    "Mise à jour système", "Création d'API", "Plateforme e-commerce", "Formation équipe", 
    "Infrastructure réseau", "Chatbot support", "Optimisation SEO"
]

PROJECT_DESC = [
    "Refonte complète du site web avec une approche responsive et moderne",
    "Développement d'une application mobile native pour Android et iOS",
    "Migration des services vers AWS avec mise en place de l'infrastructure",
    "Audit complet de la sécurité et implémentation des recommandations",
    "Intégration d'un système CRM avec les solutions existantes",
    "Automatisation des processus ERP pour optimiser les flux de travail",
    "Déploiement d'une solution de Business Intelligence",
    "Contrat de maintenance annuelle pour les systèmes informatiques",
    "Mise à jour des systèmes d'exploitation et logiciels",
    "Création d'APIs RESTful pour interconnecter les applications",
    "Développement d'une plateforme e-commerce avec passerelles de paiement",
    "Formation des équipes aux nouvelles technologies",
    "Refonte de l'infrastructure réseau et sécurisation",
    "Mise en place d'un chatbot pour le support client",
    "Optimisation du référencement naturel du site web"
]

TASK_TITLES = [
    "Analyse des besoins", "Rédaction cahier des charges", "Conception", "Développement frontend", 
    "Développement backend", "Tests unitaires", "Tests d'intégration", "Déploiement", 
    "Formation utilisateurs", "Documentation", "Support technique", "Optimisation", 
    "Correction de bugs", "Revue de code", "Tests de performance", "Mise en production"
]

TASK_DESCRIPTIONS = [
    "Analyse complète des besoins du client et des utilisateurs finaux",
    "Rédaction du cahier des charges fonctionnel et technique",
    "Conception des maquettes et de l'architecture logicielle",
    "Développement des interfaces utilisateur responsive et accessibles",
    "Développement des API et services backend nécessaires",
    "Mise en place et exécution des tests unitaires",
    "Réalisation des tests d'intégration entre les différents modules",
    "Déploiement de l'application sur l'environnement de production",
    "Formation des utilisateurs à l'utilisation de la solution",
    "Rédaction de la documentation technique et utilisateur",
    "Support technique pour résoudre les problèmes rencontrés",
    "Optimisation des performances de l'application",
    "Correction des bugs identifiés lors des tests",
    "Revue du code source et amélioration de la qualité",
    "Tests de performance pour identifier les goulots d'étranglement",
    "Mise en production finale de la solution"
]

TIME_COMMENTS = [
    "Réunion avec le client pour clarifier les besoins", 
    "Validation des maquettes avec l'équipe", 
    "Revue de code avec l'équipe technique",
    "Optimisation des requêtes SQL", 
    "Résolution du problème d'affichage sur mobile", 
    "Tests de performance",
    "Intégration avec le système existant", 
    "Documentation technique", 
    "Formation des utilisateurs",
    "Correction des bugs signalés", 
    "Amélioration de l'interface utilisateur", 
    "Déploiement sur le serveur de production"
]

COMMENT_TEXTS = [
    "J'ai terminé la première phase de développement, prêt pour une revue.",
    "Il manque quelques informations pour finaliser cette tâche.",
    "Est-ce qu'on peut prévoir une réunion pour discuter de cette fonctionnalité ?",
    "La tâche est plus complexe que prévu, j'ai besoin de plus de temps.",
    "J'ai résolu le problème en modifiant la structure de données.",
    "Le client a demandé une modification sur cette partie.",
    "Tout est terminé et testé, prêt à être déployé.",
    "J'ai ajouté des tests supplémentaires pour assurer la qualité.",
    "Il y a un conflit avec une autre fonctionnalité, à résoudre.",
    "Fonctionnalité implémentée selon les spécifications.",
    "Le client a validé cette partie lors de la démonstration.",
    "J'attends un retour de l'équipe pour continuer.",
    "Il faudrait documenter cette partie pour les utilisateurs.",
    "J'ai optimisé le code pour améliorer les performances.",
    "Une nouvelle dépendance a été ajoutée au projet."
]

# Configuration des paramètres pour la génération de données
NUM_ADMINS = 1
NUM_TECHS = 3
NUM_CLIENTS = 5
NUM_CLIENT_USERS = 8  # Utilisateurs de type client
CLIENTS_PER_USER = 3  # Nombre max de clients par utilisateur
NUM_PROJECTS_PER_CLIENT = (2, 4)  # Plage min-max
NUM_TASKS_PER_PROJECT = (5, 10)  # Plage min-max
NUM_TIME_ENTRIES = (3, 8)  # Plage min-max par tâche
NUM_COMMENTS = (1, 3)  # Plage min-max par tâche
CREDIT_INITIAL = (10, 100)  # Plage min-max pour le crédit initial des projets

def generate_admin_account(admin_email, admin_password):
    """Génère un compte administrateur avec les paramètres spécifiés"""
    admin = User(
        name="Administrateur",
        email=admin_email,
        role="admin"
    )
    admin.password_hash = bcrypt.generate_password_hash(admin_password).decode('utf-8')
    db.session.add(admin)
    db.session.flush()  # Pour obtenir l'ID généré
    
    # Créer les préférences de notification
    prefs = NotificationPreference(user_id=admin.id)
    db.session.add(prefs)
    
    print(f"Compte administrateur créé: {admin_email}")
    return admin

def generate_users():
    """Génère des utilisateurs techniciens et clients"""
    users = []
    
    # Génération des techniciens
    for i in range(NUM_TECHS):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"
        email = f"{first_name.lower()}.{last_name.lower()}@chronotrak.com"
        
        tech = User(
            name=name,
            email=email,
            role="technicien"
        )
        tech.password_hash = bcrypt.generate_password_hash("password123").decode('utf-8')
        db.session.add(tech)
        db.session.flush()  # Pour obtenir l'ID généré
        
        # Créer les préférences de notification
        prefs = NotificationPreference(user_id=tech.id)
        db.session.add(prefs)
        
        users.append(tech)
        print(f"Technicien créé: {email}")
    
    # Génération des utilisateurs clients
    client_users = []
    for i in range(NUM_CLIENT_USERS):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"
        domain = random.choice(EMAIL_DOMAINS)
        email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
        
        client_user = User(
            name=name,
            email=email,
            role="client"
        )
        client_user.password_hash = bcrypt.generate_password_hash("password123").decode('utf-8')
        db.session.add(client_user)
        db.session.flush()  # Pour obtenir l'ID généré
        
        # Créer les préférences de notification
        prefs = NotificationPreference(user_id=client_user.id)
        db.session.add(prefs)
        
        client_users.append(client_user)
        print(f"Utilisateur client créé: {email}")
    
    return users, client_users

def generate_clients():
    """Génère des clients fictifs"""
    clients_list = []
    
    for i in range(NUM_CLIENTS):
        company_name = f"{random.choice(COMPANY_NAMES)} {random.choice(COMPANY_TYPES)}"
        contact_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        
        domain = random.choice(EMAIL_DOMAINS)
        email = f"contact@{company_name.lower().replace(' ', '')}.{domain.split('.')[-1]}"
        
        phone = f"0{random.randint(1, 9)}{random.randint(10000000, 99999999)}"
        
        city = random.choice(CITIES)
        postal_code = random.choice(POSTAL_CODES)
        street = random.choice(STREET_NAMES)
        number = random.randint(1, 120)
        
        address = f"{number} {street}, {postal_code} {city}"
        
        client = Client(
            name=company_name,
            contact_name=contact_name,
            email=email,
            phone=phone,
            address=address,
            notes=f"Client créé le {datetime.now().strftime('%d/%m/%Y')} à des fins de démonstration."
        )
        
        db.session.add(client)
        db.session.flush()  # Pour obtenir l'ID généré
        clients_list.append(client)
        
        print(f"Client créé: {company_name}")
    
    return clients_list

def assign_clients_to_users(clients, client_users):
    """Assigne des clients aux utilisateurs de type client"""
    for user in client_users:
        # Sélectionner un nombre aléatoire de clients (entre 1 et CLIENTS_PER_USER)
        num_clients = random.randint(1, min(CLIENTS_PER_USER, len(clients)))
        selected_clients = random.sample(clients, num_clients)
        
        # Associer les clients à l'utilisateur
        for client in selected_clients:
            user.clients.append(client)
        
        print(f"Utilisateur {user.name} associé à {num_clients} clients")

def generate_projects(clients):
    """Génère des projets pour les clients"""
    projects_list = []
    
    for client in clients:
        # Nombre aléatoire de projets par client
        num_projects = random.randint(NUM_PROJECTS_PER_CLIENT[0], NUM_PROJECTS_PER_CLIENT[1])
        
        # Sélectionner des noms de projets aléatoires sans répétition
        selected_project_names = random.sample(PROJECT_NAMES, num_projects)
        selected_project_descs = random.sample(PROJECT_DESC, num_projects)
        
        for i in range(num_projects):
            name = selected_project_names[i]
            description = selected_project_descs[i]
            
            # Crédit initial aléatoire (en heures, convertir en minutes)
            initial_credit_hours = random.randint(CREDIT_INITIAL[0], CREDIT_INITIAL[1])
            initial_credit = initial_credit_hours * 60
            
            # Date de création aléatoire (entre 1 et 180 jours dans le passé)
            days_ago = random.randint(1, 180)
            created_at = datetime.now() - timedelta(days=days_ago)
            
            # Créer un projet avec une partie du crédit utilisé
            used_credit_hours = random.uniform(0, initial_credit_hours * 0.9)
            used_credit = int(round(used_credit_hours * 60))
            remaining_credit = initial_credit - used_credit
            
            project = Project(
                name=name,
                description=description,
                client_id=client.id,
                initial_credit=initial_credit,
                remaining_credit=remaining_credit,
                created_at=created_at
            )
            
            db.session.add(project)
            db.session.flush()  # Pour obtenir l'ID généré
            
            # Créer un log pour le crédit initial
            credit_log = CreditLog(
                project_id=project.id,
                amount=initial_credit,
                note="Crédit initial",
                created_at=created_at
            )
            db.session.add(credit_log)
            
            # Si du crédit a été utilisé, créer un log
            if used_credit > 0:
                usage_log = CreditLog(
                    project_id=project.id,
                    amount=-used_credit,
                    note="Consommation initiale",
                    created_at=created_at + timedelta(days=random.randint(1, days_ago - 1))
                )
                db.session.add(usage_log)
            
            projects_list.append(project)
            print(f"Projet créé pour {client.name}: {name} (Crédit: {remaining_credit}/{initial_credit}h)")
    
    return projects_list

def generate_tasks(projects, users):
    """Génère des tâches pour les projets"""
    all_tasks = []
    
    for project in projects:
        # Nombre aléatoire de tâches par projet
        num_tasks = random.randint(NUM_TASKS_PER_PROJECT[0], NUM_TASKS_PER_PROJECT[1])
        
        # Sélectionner des titres de tâches aléatoires sans répétition
        selected_task_titles = random.sample(TASK_TITLES, min(num_tasks, len(TASK_TITLES)))
        selected_task_descs = random.sample(TASK_DESCRIPTIONS, min(num_tasks, len(TASK_DESCRIPTIONS)))
        
        # Si besoin de plus de titres que disponibles, dupliquer certains
        while len(selected_task_titles) < num_tasks:
            selected_task_titles.append(random.choice(TASK_TITLES))
            selected_task_descs.append(random.choice(TASK_DESCRIPTIONS))
        
        # Créer les tâches
        for i in range(num_tasks):
            title = selected_task_titles[i]
            description = selected_task_descs[i]
            
            # Choisir aléatoirement le statut
            status = random.choice(['à faire', 'en cours', 'terminé'])
            
            # Choisir aléatoirement la priorité avec une pondération
            priorities = ['basse', 'normale', 'haute', 'urgente']
            weights = [0.2, 0.5, 0.2, 0.1]  # 20% basse, 50% normale, 20% haute, 10% urgente
            priority = random.choices(priorities, weights)[0]
            
            # Assigner aléatoirement à un utilisateur (ou non)
            assigned_to = random.choice([None] + users) if status != 'terminé' else random.choice(users)
            user_id = assigned_to.id if assigned_to else None
            
            # Temps estimé aléatoire entre 0.5h et 8h (convertir en minutes)
            estimated_time_hours = round(random.uniform(0.5, 8), 2)
            estimated_minutes = int(round(estimated_time_hours * 60))
            
            # Date de création entre la date de création du projet et aujourd'hui
            days_since_project = (datetime.now() - project.created_at).days
            days_ago = random.randint(1, max(1, days_since_project))
            created_at = datetime.now() - timedelta(days=days_ago)
            
            # Date de fin si la tâche est terminée
            completed_at = None
            if status == 'terminé':
                completed_days_ago = random.randint(1, max(1, days_ago - 1))
                completed_at = datetime.now() - timedelta(days=completed_days_ago)
            
            # Temps réel passé si la tâche est en cours ou terminée
            actual_time_hours = None
            actual_minutes = None
            if status in ['en cours', 'terminé']:
                # Entre 20% et 150% du temps estimé
                actual_time_hours = estimated_time_hours * random.uniform(0.2, 1.5)
                actual_minutes = int(round(actual_time_hours * 60))
            
            # Créer la tâche
            task = Task(
                title=title,
                description=description,
                status=status,
                priority=priority,
                estimated_minutes=estimated_minutes,
                actual_minutes=actual_minutes,
                project_id=project.id,
                user_id=user_id,
                created_at=created_at,
                completed_at=completed_at
            )
            
            db.session.add(task)
            db.session.flush()  # Pour obtenir l'ID généré
            all_tasks.append(task)
            
            print(f"Tâche créée pour {project.name}: {title} ({status}, {priority})")
    
    return all_tasks

def generate_time_entries(tasks, users):
    """Génère des entrées de temps pour les tâches"""
    for task in tasks:
        if task.status in ['en cours', 'terminé'] and task.actual_minutes:
            # Nombre aléatoire d'entrées de temps
            num_entries = random.randint(NUM_TIME_ENTRIES[0], NUM_TIME_ENTRIES[1])
            
            # S'assurer que le temps total correspond à actual_minutes
            total_time_needed_minutes = task.actual_minutes
            
            # Répartir le temps entre les entrées
            remaining_entries = num_entries
            remaining_time = total_time_needed_minutes
            
            for i in range(num_entries):
                # Calculer le temps pour cette entrée
                if remaining_entries > 1:
                    # Pour toutes les entrées sauf la dernière, prendre une portion aléatoire
                    time_portion = min(int(remaining_time * random.uniform(0.1, 0.5)), remaining_time)
                else:
                    # Pour la dernière entrée, prendre tout le temps restant
                    time_portion = remaining_time
                
                minutes = int(round(time_portion))
                remaining_time -= minutes
                remaining_entries -= 1
                
                # S'assurer qu'on ne dépasse pas le temps total
                if minutes <= 0:
                    continue
                
                # Date de création entre la date de création de la tâche et aujourd'hui ou date de complétion
                end_date = task.completed_at if task.completed_at else datetime.now()
                days_range = (end_date - task.created_at).days
                if days_range <= 0:
                    days_range = 1
                
                days_ago = random.randint(1, days_range)
                created_at = end_date - timedelta(days=days_ago)
                
                # Choisir un utilisateur aléatoire parmi les techniciens
                user = task.assigned_to if task.assigned_to else random.choice(users)
                
                # Commentaire aléatoire (ou aucun)
                description = random.choice([None] + TIME_COMMENTS)
                
                time_entry = TimeEntry(
                    task_id=task.id,
                    user_id=user.id,
                    minutes=minutes,
                    description=description,
                    created_at=created_at
                )
                
                db.session.add(time_entry)
            
            print(f"Entrées de temps générées pour la tâche {task.id}: {num_entries} entrées pour {total_time_needed_minutes} min")

def generate_comments(tasks, users, client_users):
    """Génère des commentaires pour les tâches"""
    all_users = users + client_users
    
    for task in tasks:
        # Nombre aléatoire de commentaires
        num_comments = random.randint(NUM_COMMENTS[0], NUM_COMMENTS[1])
        
        # Période entre la création de la tâche et sa complétion ou aujourd'hui
        end_date = task.completed_at if task.completed_at else datetime.now()
        time_span = (end_date - task.created_at).total_seconds()
        
        # Créer les commentaires
        for i in range(num_comments):
            # Sélectionner un texte de commentaire aléatoire
            content = random.choice(COMMENT_TEXTS)
            
            # Choisir aléatoirement un utilisateur pour ce commentaire
            user = random.choice(all_users)
            
            # Date de création aléatoire entre la création de la tâche et sa fin ou aujourd'hui
            seconds_ago = random.uniform(0, time_span)
            created_at = end_date - timedelta(seconds=seconds_ago)
            
            comment = Comment(
                content=content,
                task_id=task.id,
                user_id=user.id,
                created_at=created_at
            )
            
            db.session.add(comment)
        
        if num_comments > 0:
            print(f"Commentaires générés pour la tâche {task.id}: {num_comments} commentaires")

def create_database(db_path=None):
    """Crée et initialise la base de données avec des données de démo"""
    # Configurer le chemin de la base de données si spécifié
    if db_path:
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    
    # Créer l'application Flask avec le contexte
    app = create_app('development')
    
    with app.app_context():
        try:
            # Supprimer et recréer les tables
            db.drop_all()
            db.create_all()
            
            print("\n=== Génération de la base de données de démonstration ===\n")
            
            admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@chronotrak.com')
            admin_password = current_app.config.get('ADMIN_PASSWORD', 'admin123')
            
            # Générer un admin
            admin = generate_admin_account(admin_email, admin_password)
            
            # Génération des utilisateurs
            users, client_users = generate_users()
            
            # Génération des clients
            clients = generate_clients()
            
            # Assignation des clients aux utilisateurs
            assign_clients_to_users(clients, client_users)
            
            # Générer des projets
            projects = generate_projects(clients)
            
            # Générer des tâches
            tasks = generate_tasks(projects, users)
            
            # Générer des entrées de temps
            generate_time_entries(tasks, users)
            
            # Générer des commentaires
            generate_comments(tasks, users, client_users)
            
            # Enregistrer toutes les modifications
            db.session.commit()
            
            print("\n=== Génération terminée avec succès ===\n")
            print(f"Statistiques :")
            print(f"- {NUM_ADMINS} administrateur")
            print(f"- {NUM_TECHS} techniciens")
            print(f"- {NUM_CLIENT_USERS} utilisateurs clients")
            print(f"- {NUM_CLIENTS} clients")
            print(f"- {len(projects)} projets")
            print(f"- {len(tasks)} tâches")
            
            # Afficher les identifiants de connexion
            print("\n=== Identifiants de connexion ===\n")
            print(f"Admin: {admin_email} / {admin_password}")
            print("Autres utilisateurs: <email> / password123")
            
            db_location = db_path or os.path.join(app.instance_path, 'chronotrak.db')
            print(f"\nBase de données créée avec succès à l'emplacement: {db_location}")
            
            return True
        
        except Exception as e:
            print(f"Erreur lors de la création de la base de données: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    # Analyse des arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Génère une base de données de démonstration pour ChronoTrak")
    parser.add_argument('--output', help="Chemin du fichier de base de données à créer")
    args = parser.parse_args()
    
    start_time = time.time()
    
    # Créer la base de données
    success = create_database(args.output)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    if success:
        print(f"\nTemps d'exécution: {elapsed:.2f} secondes")
        sys.exit(0)
    else:
        sys.exit(1)