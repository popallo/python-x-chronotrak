# Management Scripts

Ce répertoire contient les scripts de gestion et d'automatisation pour ChronoTrak.

## Scripts disponibles

### `auto_archive_tasks.py`
Script d'archivage automatique des tâches terminées depuis plus de 2 semaines.

**Utilisation :**
```bash
# Exécution manuelle
python management/auto_archive_tasks.py

# Ou via Flask CLI
flask auto-archive
```

### `setup_cron.sh`
Script de configuration du cron job pour l'archivage automatique.

**Utilisation :**
```bash
# Dans le conteneur Docker
./management/setup_cron.sh
```

## Configuration automatique

Le cron job est configuré pour s'exécuter tous les jours à 2h du matin :
```
0 2 * * * cd /app && flask auto-archive >> /var/log/chronotrak_archive.log 2>&1
```

## Logs

Les logs d'archivage automatique sont disponibles dans :
- `/var/log/chronotrak_archive.log` (dans le conteneur)

## Sécurité

- Les scripts sont versionnés et peuvent être audités
- Le répertoire `scripts/` reste non versionné pour la sécurité
- Seuls les scripts nécessaires sont inclus dans le versioning
