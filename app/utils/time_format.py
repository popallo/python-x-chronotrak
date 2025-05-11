def format_time(value):
    """Formate un nombre d'heures en format h min"""
    if value is None:
        return ""
    
    # S'assurer que la valeur est un flottant et l'arrondir à 4 décimales pour éviter les erreurs de précision
    value = round(float(value), 4)
    
    # Convertir en minutes totales et arrondir
    total_minutes = round(value * 60)
    
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

def generate_hour_options(extra_blocks=None, include_undefined=False):
    """
    Génère des options horaires pour les SelectField (5min à 8h + blocs supplémentaires).
    :param extra_blocks: liste de tuples (valeur, label) à ajouter à la fin
    :param include_undefined: si True, ajoute '-- Non défini --' au début
    """
    hours_options = []
    for i in range(1, 13):
        minutes = i * 5
        decimal_value = round(minutes / 60, 2)
        label = f"{minutes} min" if minutes < 60 else "1h"
        hours_options.append((decimal_value, label))
    for i in range(5, 32):
        hour = i // 4
        minute = (i % 4) * 15
        decimal_value = round(hour + minute / 60, 2)
        label = f"{hour}h {minute}min" if minute > 0 else f"{hour}h"
        hours_options.append((decimal_value, label))
    if extra_blocks:
        hours_options.extend(extra_blocks)
    if include_undefined:
        hours_options = [(0.0, '-- Non défini --')] + hours_options
    return hours_options