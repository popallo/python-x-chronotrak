def format_time(value):
    """Formate un nombre de minutes en format h min"""
    if value is None:
        return ""

    # Gérer les valeurs négatives
    is_negative = value < 0
    abs_value = abs(value)

    # S'assurer que la valeur est un entier
    # Si la valeur est un float et > 100, c'est probablement déjà en minutes
    # Sinon, c'est probablement en heures
    if isinstance(abs_value, float) and abs_value > 100:
        total_minutes = int(round(abs_value))
    elif isinstance(abs_value, float):
        total_minutes = int(round(abs_value * 60))
    else:
        total_minutes = int(abs_value)

    # Calculer les heures et minutes
    hours = total_minutes // 60
    minutes = total_minutes % 60

    # Formater selon le cas
    if hours > 0:
        if minutes > 0:
            result = f"{hours}h{minutes}min"
        else:
            result = f"{hours}h"
    else:
        result = f"{minutes}min"

    # Ajouter le signe négatif si nécessaire
    return f"-{result}" if is_negative else result


def generate_hour_options(extra_blocks=None, include_undefined=False):
    """
    Génère des options horaires pour les SelectField (1min à 8h + blocs supplémentaires).
    :param extra_blocks: liste de tuples (valeur, label) à ajouter à la fin
    :param include_undefined: si True, ajoute '-- Non défini --' au début
    """
    hours_options = []

    # Ajouter les options de 1 à 5 minutes
    for minutes in range(1, 6):
        decimal_value = minutes / 60  # Pas de round() pour éviter les erreurs d'arrondi
        hours_options.append((decimal_value, f"{minutes} min"))

    # Ajouter les options par tranches de 5 minutes (10, 15, 20, 25, 30, 35, 40, 45, 50, 55)
    for minutes in range(10, 60, 5):
        decimal_value = minutes / 60
        hours_options.append((decimal_value, f"{minutes} min"))

    # Ajouter les options par tranches de 15 minutes pour les heures (1h, 1h15, 1h30, 1h45, 2h, etc.)
    for hour in range(1, 9):  # 1h à 8h
        for quarter in range(4):  # 0, 15, 30, 45 minutes
            total_minutes = hour * 60 + quarter * 15
            decimal_value = total_minutes / 60

            if quarter == 0:
                label = f"{hour}h"
            else:
                label = f"{hour}h{quarter * 15}min"

            hours_options.append((decimal_value, label))

    if extra_blocks:
        hours_options.extend(extra_blocks)
    if include_undefined:
        hours_options = [(0.0, "-- Non défini --")] + hours_options
    return hours_options
