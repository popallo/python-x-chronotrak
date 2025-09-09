#!/bin/bash

# Script de configuration du cron pour l'archivage automatique des tâches
# Ce script configure le cron job pour exécuter l'archivage automatique tous les jours à 2h du matin

echo "Configuration du cron job pour l'archivage automatique des tâches..."

# Créer le fichier cron temporaire
CRON_FILE="/tmp/chronotrak_cron"

# Ajouter la tâche cron (archivage automatique tous les jours à 2h du matin)
echo "0 2 * * * cd /app && flask auto-archive >> /var/log/chronotrak_archive.log 2>&1" > $CRON_FILE

# Ajouter la tâche cron au crontab de l'utilisateur root
crontab $CRON_FILE

# Vérifier que la tâche a été ajoutée
echo "Tâches cron configurées :"
crontab -l

# Nettoyer le fichier temporaire
rm $CRON_FILE

echo "Configuration terminée ! L'archivage automatique s'exécutera tous les jours à 2h du matin."
echo "Les logs seront disponibles dans /var/log/chronotrak_archive.log"
