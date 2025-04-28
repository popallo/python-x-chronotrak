def format_time(value):
    """Formate un nombre d'heures en format h min"""
    if value is None:
        return ""
    
    # Convertir en minutes totales
    total_minutes = int(value * 60)
    
    # Calculer les heures et minutes
    hours = total_minutes // 60
    minutes = total_minutes % 60
    
    # Formater selon le cas
    if hours > 0:
        if minutes > 0:
            return f"{hours}h{minutes}min"
        else:
            return f"{hours}h"
    else:
        return f"{minutes}min"