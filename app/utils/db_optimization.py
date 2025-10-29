from flask import current_app
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configure SQLite pour de meilleures performances via PRAGMA"""
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        
        # Optimisations de performance
        cursor.execute("PRAGMA cache_size = -64000")  # 64MB de cache
        cursor.execute("PRAGMA journal_mode = WAL")   # Mode WAL pour de meilleures performances
        cursor.execute("PRAGMA synchronous = NORMAL") # Équilibre performance/sécurité
        cursor.execute("PRAGMA temp_store = MEMORY")  # Stockage temporaire en mémoire
        cursor.execute("PRAGMA mmap_size = 268435456") # 256MB de mmap
        
        # Optimisations de sécurité
        cursor.execute("PRAGMA foreign_keys = ON")    # Contraintes de clés étrangères
        cursor.execute("PRAGMA secure_delete = OFF")  # Performance vs sécurité
        
        cursor.close()
