import re

from unidecode import unidecode


def generate_slug(text, model_class, existing_id=None):
    """
    Génère un slug unique à partir d'un texte.

    Args:
        text (str): Le texte à convertir en slug
        model_class: La classe du modèle pour vérifier l'unicité
        existing_id: L'ID de l'objet existant (pour la mise à jour)

    Returns:
        str: Un slug unique
    """
    # Convertir en minuscules et remplacer les caractères accentués
    slug = unidecode(text.lower())

    # Remplacer les espaces et caractères spéciaux par des tirets
    slug = re.sub(r"[^a-z0-9]+", "-", slug)

    # Supprimer les tirets au début et à la fin
    slug = slug.strip("-")

    # Vérifier si le slug existe déjà
    base_slug = slug
    counter = 1

    while True:
        # Construire la requête
        query = model_class.query.filter_by(slug=slug)

        # Si on met à jour un objet existant, exclure son ID
        if existing_id is not None:
            query = query.filter(model_class.id != existing_id)

        # Vérifier si le slug existe
        if not query.first():
            break

        # Si le slug existe, ajouter un numéro
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


def update_slug(model_instance):
    """
    Met à jour le slug d'une instance de modèle.

    Args:
        model_instance: L'instance du modèle à mettre à jour
    """
    # Déterminer le texte source en fonction du type de modèle
    if hasattr(model_instance, "name"):
        text = model_instance.name
    elif hasattr(model_instance, "title"):
        text = model_instance.title
    else:
        raise ValueError("Le modèle doit avoir un attribut 'name' ou 'title'")

    # Générer le nouveau slug
    model_instance.slug = generate_slug(text, type(model_instance), model_instance.id)
