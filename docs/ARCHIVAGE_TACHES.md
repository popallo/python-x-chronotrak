# Système d'Archivage des Tâches

## Vue d'ensemble

Le système d'archivage des tâches permet de nettoyer automatiquement le kanban en déplaçant les tâches terminées depuis plus de 2 semaines vers une section d'archives. Cela évite que le kanban soit "pollué" par de nombreuses tâches terminées tout en conservant un accès consultatif à ces informations.

## Fonctionnalités

### 1. Archivage Automatique
- **Déclenchement** : Tâches terminées depuis plus de 2 semaines
- **Commande CLI** : `flask auto-archive`
- **Script autonome** : `scripts/auto_archive_tasks.py`

### 2. Archivage Manuel
- **Bouton d'archivage** : Disponible sur les tâches terminées
- **Bouton de désarchivage** : Disponible sur les tâches archivées
- **Interface** : Boutons dans la barre d'actions des tâches

### 3. Consultation des Archives
- **Route** : `/archives`
- **Navigation** : Lien "Archives" dans le menu principal
- **Filtres** : Par projet et recherche textuelle
- **Pagination** : 20 tâches par page

## Utilisation

### Archivage Automatique via Cron

Pour automatiser l'archivage, ajoutez cette ligne à votre crontab :

```bash
# Archivage automatique tous les jours à 2h du matin
0 2 * * * cd /path/to/chronotrak && source .venv/bin/activate && flask auto-archive
```

### Archivage Manuel

1. **Archiver une tâche** :
   - Aller sur la page de détail de la tâche
   - Cliquer sur le bouton d'archivage (icône archive)
   - Confirmer l'action

2. **Désarchiver une tâche** :
   - Aller dans la section Archives
   - Cliquer sur le bouton de désarchivage (icône undo)
   - Confirmer l'action

### Consultation des Archives

1. **Accès** : Cliquer sur "Archives" dans le menu principal
2. **Filtrage** : Utiliser les filtres par projet ou recherche textuelle
3. **Navigation** : Utiliser la pagination pour parcourir les archives

## Modifications Techniques

### Base de Données

Nouveaux champs ajoutés à la table `task` :
- `is_archived` : Boolean (défaut: False)
- `archived_at` : DateTime (nullable)

### Modèle Task

Nouvelles méthodes :
- `archive()` : Archive la tâche
- `unarchive()` : Désarchive la tâche
- `should_be_archived()` : Retourne les tâches à archiver
- `auto_archive_old_tasks()` : Archive automatiquement les tâches

### Routes

Nouvelles routes :
- `GET /archives` : Page des archives
- `POST /tasks/<id>/archive` : Archiver une tâche
- `POST /tasks/<id>/unarchive` : Désarchiver une tâche

### Templates

Nouveaux templates :
- `tasks/archives.html` : Page des archives

Modifications :
- `layout.html` : Ajout du lien Archives
- `task_detail.html` : Boutons d'archivage/désarchivage

## Configuration

### Variables d'Environnement

Aucune configuration supplémentaire requise. Le système utilise la configuration existante de l'application.

### Permissions

- **Archivage** : Tous les utilisateurs authentifiés
- **Désarchivage** : Tous les utilisateurs authentifiés
- **Consultation** : Tous les utilisateurs authentifiés

## Maintenance

### Vérification du Système

```bash
# Vérifier les tâches à archiver
flask shell
>>> from app.models.task import Task
>>> Task.should_be_archived()

# Exécuter l'archivage manuel
flask auto-archive
```

### Logs

Les logs d'archivage sont affichés dans la console lors de l'exécution de la commande CLI.

## Dépannage

### Problèmes Courants

1. **Migration échouée** :
   ```bash
   flask db upgrade
   ```

2. **Permissions insuffisantes** :
   Vérifier que l'utilisateur a les droits d'écriture sur la base de données

3. **Tâches non archivées** :
   Vérifier que les tâches ont bien le statut "terminé" et une date de completion

### Support

Pour toute question ou problème, consulter les logs de l'application ou contacter l'équipe de développement.
