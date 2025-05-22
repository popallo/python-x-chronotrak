from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.types import TypeDecorator, String
from flask import current_app
import base64
import logging

logger = logging.getLogger(__name__)

class EncryptedType(TypeDecorator):
    """Type SQLAlchemy pour les champs chiffrés"""
    impl = String(500)  # Augmentation de la taille pour stocker les données chiffrées
    cache_ok = False    # Important pour éviter les problèmes de cache

    def process_bind_param(self, value, dialect):
        """Chiffre la valeur avant de l'envoyer à la base de données"""
        if value is None:
            return None
        
        try:
            key = current_app.config.get('ENCRYPTION_KEY')
            if not key:
                logger.error("Clé de chiffrement manquante dans la configuration")
                return value  # Retourner la valeur telle quelle si pas de clé
                
            f = Fernet(key)
            encrypted_data = f.encrypt(value.encode('utf-8'))
            return encrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement: {str(e)}")
            logger.error(f"Valeur à chiffrer: {value[:20]}...")
            return value  # En cas d'erreur, retourner la valeur non chiffrée

    def process_result_value(self, value, dialect):
        """Déchiffre la valeur récupérée de la base de données"""
        if value is None:
            return None

        try:
            # Tester si la valeur semble être chiffrée (commence par 'gAAA')
            if not isinstance(value, str) or not value.startswith('gAAA'):
                logger.warning(f"Valeur non chiffrée détectée: {value[:20]}...")
                return value
                
            key = current_app.config.get('ENCRYPTION_KEY')
            if not key:
                logger.error("Clé de chiffrement manquante dans la configuration")
                return "[Erreur: Clé de chiffrement manquante]"
                
            f = Fernet(key)
            decrypted_data = f.decrypt(value.encode('utf-8'))
            return decrypted_data.decode('utf-8')
        except InvalidToken:
            logger.error(f"Impossible de déchiffrer la valeur. Token invalide ou mauvaise clé.")
            logger.error(f"Valeur chiffrée: {value[:20]}...")
            logger.error(f"Clé utilisée: {key[:10]}...")
            return "[Erreur de déchiffrement]"
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement: {str(e)}")
            logger.error(f"Valeur chiffrée: {value[:20]}...")
            return "[Erreur de déchiffrement]"