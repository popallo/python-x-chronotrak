#!/usr/bin/env python3
"""
Script de chiffrement pour la PRODUCTION
⚠️  ATTENTION: À exécuter avec précaution en production
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def is_encrypted(value):
    """Vérifie si une valeur semble déjà être chiffrée"""
    if not value:
        return True
    return isinstance(value, str) and value.startswith('gAAA')

def main():
    # Vérifications de sécurité
    print("🚨 SCRIPT DE CHIFFREMENT POUR PRODUCTION 🚨")
    print("=" * 50)
    
    # Vérifier la clé de chiffrement
    encryption_key = os.environ.get('ENCRYPTION_KEY')
    if not encryption_key:
        print("❌ ERREUR: ENCRYPTION_KEY non définie!")
        return 1
    
    # Vérifier l'environnement
    env = os.environ.get('FLASK_ENV', 'development')
    if env != 'production':
        print(f"⚠️  ATTENTION: Environnement détecté: {env}")
        print("Ce script est conçu pour la production.")
        response = input("Continuer quand même? (oui/non): ")
        if response.lower() != 'oui':
            print("Abandon.")
            return 1
    
    print("✅ Vérifications de sécurité passées")
    print("📋 Ce script va:")
    print("   - Chiffrer les données non chiffrées")
    print("   - Limiter les warnings d'encryption")
    print("   - Sauvegarder les modifications")
    
    response = input("\n🤔 Confirmer l'exécution? (oui/non): ")
    if response.lower() != 'oui':
        print("Abandon.")
        return 1
    
    try:
        from app import create_app, db
        from app.models.client import Client
        from app.models.task import Comment
        from app.models.communication import Communication
        from cryptography.fernet import Fernet
        
        # Créer l'application avec le contexte
        app = create_app('production')
        
        with app.app_context():
            print("\n🔧 Initialisation...")
            fernet = Fernet(encryption_key.encode('utf-8'))
            
            total_encrypted = 0
            
            # 1. Chiffrer les clients (par petits lots)
            print("\n📊 Traitement des clients...")
            clients = Client.query.all()
            client_encrypted = 0
            
            for i, client in enumerate(clients):
                fields_to_encrypt = ['email', 'phone', 'address', 'notes']
                for field in fields_to_encrypt:
                    value = getattr(client, field)
                    if value and not is_encrypted(value):
                        encrypted_value = fernet.encrypt(value.encode('utf-8')).decode('utf-8')
                        setattr(client, field, encrypted_value)
                        client_encrypted += 1
                
                # Commit par lots de 10 pour éviter les timeouts
                if (i + 1) % 10 == 0:
                    db.session.commit()
                    print(f"   ✅ {i + 1}/{len(clients)} clients traités")
            
            if client_encrypted > 0:
                print(f"   🔐 {client_encrypted} champs clients chiffrés")
                total_encrypted += client_encrypted
            
            # 2. Chiffrer les commentaires
            print("\n💬 Traitement des commentaires...")
            comments = Comment.query.all()
            comment_encrypted = 0
            
            for i, comment in enumerate(comments):
                if comment.content and not is_encrypted(comment.content):
                    encrypted_content = fernet.encrypt(comment.content.encode('utf-8')).decode('utf-8')
                    comment.content = encrypted_content
                    comment_encrypted += 1
                
                # Commit par lots de 50
                if (i + 1) % 50 == 0:
                    db.session.commit()
                    print(f"   ✅ {i + 1}/{len(comments)} commentaires traités")
            
            if comment_encrypted > 0:
                print(f"   🔐 {comment_encrypted} commentaires chiffrés")
                total_encrypted += comment_encrypted
            
            # 3. Chiffrer les communications
            print("\n📧 Traitement des communications...")
            communications = Communication.query.all()
            comm_encrypted = 0
            
            for i, comm in enumerate(communications):
                fields_to_encrypt = ['content_html', 'content_text']
                for field in fields_to_encrypt:
                    value = getattr(comm, field)
                    if value and not is_encrypted(value):
                        encrypted_value = fernet.encrypt(value.encode('utf-8')).decode('utf-8')
                        setattr(comm, field, encrypted_value)
                        comm_encrypted += 1
                
                # Commit par lots de 25
                if (i + 1) % 25 == 0:
                    db.session.commit()
                    print(f"   ✅ {i + 1}/{len(communications)} communications traitées")
            
            if comm_encrypted > 0:
                print(f"   🔐 {comm_encrypted} champs de communication chiffrés")
                total_encrypted += comm_encrypted
            
            # Commit final
            print("\n💾 Sauvegarde finale...")
            db.session.commit()
            
            if total_encrypted > 0:
                print(f"\n🎉 SUCCÈS: {total_encrypted} champs chiffrés!")
                print("✅ Les warnings d'encryption ont été résolus")
                print("✅ L'application peut maintenant être redémarrée")
            else:
                print("\n✅ Aucune donnée à chiffrer - tout est déjà chiffré")
            
            return 0
            
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        print("🔄 Rollback automatique...")
        db.session.rollback()
        return 1

if __name__ == "__main__":
    exit(main())
