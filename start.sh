#!/bin/bash

# Script de démarrage pour ChronoTrak (web uniquement)

echo "Démarrage de ChronoTrak..."

# Vérifier l'environnement
FLASK_ENV=${FLASK_ENV:-development}
echo "Environnement détecté : $FLASK_ENV"

echo "Note: les tâches cron (ex: auto-archive) doivent être gérées par un conteneur/service dédié (ex: docker-compose service 'cron') ou par le cron de l'hôte."

# Démarrer l'application Flask
echo "Démarrage de l'application Flask..."
exec gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 4 \
  --worker-class sync \
  --worker-connections 1000 \
  --timeout 60 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --preload \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --capture-output \
  --enable-stdio-inheritance \
  wsgi:app
