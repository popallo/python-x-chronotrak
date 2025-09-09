#!/bin/bash

# Script de démarrage pour ChronoTrak avec configuration automatique du cron

echo "Démarrage de ChronoTrak..."

# Démarrer le service cron en arrière-plan
echo "Démarrage du service cron..."
crond -f -d 8 &

# Attendre un peu que cron démarre
sleep 2

# Configurer le cron job pour l'archivage automatique
echo "Configuration du cron job d'archivage automatique..."
./management/setup_cron.sh

# Démarrer l'application Flask
echo "Démarrage de l'application Flask..."
exec gunicorn --bind 0.0.0.0:5000 wsgi:app
