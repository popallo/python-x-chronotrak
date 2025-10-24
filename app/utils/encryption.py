from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.types import TypeDecorator, String
from flask import current_app
import base64
import logging

logger = logging.getLogger(__name__)

# Cache pour éviter les warnings répétés pour les mêmes valeurs
_warned_values = set()
_warning_count = 0
_MAX_WARNINGS = 10  # Limite le nombre total de warnings

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
            
            # Chiffrement simple sans timeout (plus compatible)
            f = Fernet(key)
            encrypted_data = f.encrypt(value.encode('utf-8'))
            return encrypted_data.decode('utf-8')
                
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement: {str(e)}")
            # Ne pas logger la valeur pour éviter les fuites d'informations
            return value  # En cas d'erreur, retourner la valeur non chiffrée

    def process_result_value(self, value, dialect):
        """Déchiffre la valeur récupérée de la base de données"""
        if value is None:
            return None

        try:
            # Tester si la valeur semble être chiffrée (commence par 'gAAA')
            if not isinstance(value, str) or not value.startswith('gAAA'):
                # Ignorer les warnings pour les valeurs vides ou composées uniquement d'espaces
                if not value or value.strip() == '':
                    return value
                
                # Limiter le nombre de warnings pour éviter le spam
                global _warning_count
                if _warning_count < _MAX_WARNINGS:
                    value_hash = hash(value)
                    if value_hash not in _warned_values:
                        logger.warning(f"Valeur non chiffrée détectée: {value[:20]}...")
                        _warned_values.add(value_hash)
                        _warning_count += 1
                elif _warning_count == _MAX_WARNINGS:
                    logger.warning(f"Limite de {_MAX_WARNINGS} warnings d'encryption atteinte. Les warnings suivants seront ignorés.")
                    _warning_count += 1
                return value
            
            # La valeur est chiffrée, procéder au déchiffrement simple
            key = current_app.config.get('ENCRYPTION_KEY')
            if not key:
                logger.error("Clé de chiffrement manquante dans la configuration")
                return "[Erreur: Clé de chiffrement manquante]"
            
            f = Fernet(key)
            decrypted_data = f.decrypt(value.encode('utf-8'))
            return decrypted_data.decode('utf-8')
                
        except InvalidToken:
            logger.error("Impossible de déchiffrer la valeur. Token invalide ou mauvaise clé.")
            return "[Erreur de déchiffrement]"
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement: {str(e)}")
            return "[Erreur de déchiffrement]"