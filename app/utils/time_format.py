def format_time(value):
    """Formate un nombre de minutes en format h min"""
    if value is None:
        return ""
    
    # S'assurer que la valeur est un entier
    total_minutes = int(round(float(value) * 60)) if isinstance(value, float) else int(value)
    
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
    Génère des options horaires pour les SelectField (1min à 8h + blocs supplémentaires).
    :param extra_blocks: liste de tuples (valeur, label) à ajouter à la fin
    :param include_undefined: si True, ajoute '-- Non défini --' au début
    """
    hours_options = []
    # Ajouter les options de 1 à 5 minutes
    for minutes in range(1, 6):
        decimal_value = round(minutes / 60, 2)
        hours_options.append((decimal_value, f"{minutes} min"))
    # Ajouter les options par tranches de 5 minutes
    for i in range(2, 13):  # Commence à 2 car on a déjà ajouté 5 minutes
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