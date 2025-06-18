#!/usr/bin/env python3
"""
Script pour vérifier les communications envoyées et leurs destinataires
"""

import os
import sys
from datetime import datetime, timedelta

# Ajouter le répertoire parent au path pour pouvoir importer l'application
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.communication import Communication
from app.models.user import User
from app.models.project import Project
from app.models.task import Task

def check_recent_communications(hours=24):
    """Vérifie les communications envoyées dans les dernières heures"""
    
    # Créer l'application
    app = create_app('development')
    
    with app.app_context():
        print(f"=== Communications envoyées dans les dernières {hours} heures ===\n")
        
        # Calculer la date limite
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Récupérer les communications récentes
        communications = Communication.query.filter(
            Communication.sent_at >= since
        ).order_by(Communication.sent_at.desc()).all()
        
        if not communications:
            print("Aucune communication trouvée dans cette période.")
            return
        
        print(f"Nombre de communications trouvées: {len(communications)}\n")
        
        # Grouper par type
        by_type = {}
        for comm in communications:
            if comm.type not in by_type:
                by_type[comm.type] = []
            by_type[comm.type].append(comm)
        
        for email_type, comms in by_type.items():
            print(f"--- Type: {email_type} ({len(comms)} communications) ---")
            
            for comm in comms:
                print(f"  📧 {comm.subject}")
                print(f"     Destinataire: {comm.recipient}")
                print(f"     Envoyé: {comm.sent_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"     Statut: {comm.status}")
                
                if comm.project_id:
                    project = Project.query.get(comm.project_id)
                    if project:
                        print(f"     Projet: {project.name} (Client: {project.client.name})")
                
                if comm.task_id:
                    task = Task.query.get(comm.task_id)
                    if task:
                        print(f"     Tâche: {task.title}")
                
                if comm.user_id:
                    user = User.query.get(comm.user_id)
                    if user:
                        print(f"     Utilisateur: {user.name} ({user.role})")
                
                print()
        
        # Analyse des destinataires
        print("=== Analyse des destinataires ===")
        
        # Récupérer tous les utilisateurs
        admins = User.query.filter_by(role='admin').all()
        clients = User.query.filter_by(role='client').all()
        
        admin_emails = [admin.email for admin in admins if admin.email]
        client_emails = [client.email for client in clients if client.email]
        
        print(f"Administrateurs: {admin_emails}")
        print(f"Clients: {client_emails}")
        
        # Vérifier les communications par destinataire
        recipients = {}
        for comm in communications:
            if comm.recipient not in recipients:
                recipients[comm.recipient] = []
            recipients[comm.recipient].append(comm)
        
        print(f"\nCommunications par destinataire:")
        for recipient, comms in recipients.items():
            user = User.query.filter_by(email=recipient).first()
            role = user.role if user else "Externe"
            print(f"  {recipient} ({role}): {len(comms)} communications")
            
            # Afficher les types d'emails reçus
            types = set(comm.type for comm in comms)
            print(f"    Types: {', '.join(types)}")

def check_email_rules_compliance():
    """Vérifie la conformité aux nouvelles règles d'emails"""
    
    app = create_app('development')
    
    with app.app_context():
        print("=== Vérification de la conformité aux règles d'emails ===\n")
        
        # Récupérer les communications récentes (dernières 24h)
        since = datetime.utcnow() - timedelta(hours=24)
        communications = Communication.query.filter(
            Communication.sent_at >= since
        ).order_by(Communication.sent_at.desc()).all()
        
        if not communications:
            print("Aucune communication récente à analyser.")
            return
        
        # Récupérer les administrateurs
        admins = User.query.filter_by(role='admin').all()
        admin_emails = [admin.email for admin in admins if admin.email]
        
        print(f"Administrateurs: {admin_emails}")
        
        # Analyser chaque communication
        issues = []
        
        for comm in communications:
            # Vérifier si c'est en production (pas de préfixe [DEV])
            is_production = not comm.subject.startswith('[DEV]')
            
            if is_production:
                # Règle: Les administrateurs doivent recevoir tous les emails sauf s'ils sont les seuls destinataires
                
                # Trouver tous les destinataires pour cette communication
                same_time_comms = Communication.query.filter(
                    Communication.sent_at == comm.sent_at,
                    Communication.subject == comm.subject,
                    Communication.type == comm.type
                ).all()
                
                recipients = [c.recipient for c in same_time_comms]
                
                # Vérifier si les administrateurs sont présents
                admin_recipients = [r for r in recipients if r in admin_emails]
                non_admin_recipients = [r for r in recipients if r not in admin_emails]
                
                if non_admin_recipients and not admin_recipients:
                    issues.append({
                        'type': 'admin_missing',
                        'subject': comm.subject,
                        'recipients': recipients,
                        'message': 'Administrateurs manquants en copie'
                    })
                
                # Vérifier les emails liés à des projets
                if comm.project_id:
                    project = Project.query.get(comm.project_id)
                    if project:
                        # Vérifier si le client du projet reçoit l'email
                        client_users = User.query.filter_by(role='client').all()
                        client_emails = []
                        for client_user in client_users:
                            if client_user.has_access_to_client(project.client_id):
                                client_emails.append(client_user.email)
                        
                        project_client_recipients = [r for r in recipients if r in client_emails]
                        
                        if not project_client_recipients and client_emails:
                            issues.append({
                                'type': 'client_missing',
                                'subject': comm.subject,
                                'project': project.name,
                                'client_emails': client_emails,
                                'recipients': recipients,
                                'message': 'Client du projet manquant'
                            })
        
        if issues:
            print("❌ Problèmes détectés:")
            for issue in issues:
                print(f"\n  - {issue['message']}")
                print(f"    Sujet: {issue['subject']}")
                print(f"    Destinataires: {issue['recipients']}")
                if 'project' in issue:
                    print(f"    Projet: {issue['project']}")
                if 'client_emails' in issue:
                    print(f"    Emails clients attendus: {issue['client_emails']}")
        else:
            print("✅ Aucun problème détecté - toutes les règles sont respectées!")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Vérifier les communications envoyées')
    parser.add_argument('--hours', type=int, default=24, help='Nombre d\'heures à analyser (défaut: 24)')
    parser.add_argument('--compliance', action='store_true', help='Vérifier la conformité aux règles')
    
    args = parser.parse_args()
    
    if args.compliance:
        check_email_rules_compliance()
    else:
        check_recent_communications(args.hours) 