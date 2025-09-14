#!/bin/bash

# Script de démarrage pour ChronoTrak avec cron

echo "Démarrage de ChronoTrak..."

# Démarrer le service cron en arrière-plan
echo "Démarrage du service cron..."
crond -f -d 8 &

# Attendre un peu que cron démarre
sleep 2

# Vérifier que le cron job est configuré
echo "Vérification du cron job d'archivage automatique..."
if [ -f /etc/cron.d/chronotrak-archive ]; then
    echo "Cron job configuré :"
    cat /etc/cron.d/chronotrak-archive
else
    echo "Avertissement : Cron job non trouvé"
fi

# Démarrer l'application Flask
echo "Démarrage de l'application Flask..."
exec gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 4 \
  --worker-class sync \
  --worker-connections 1000 \
  --timeout 30 \
  --keep-alive 2 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --preload \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  wsgi:app
