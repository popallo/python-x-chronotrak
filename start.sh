#!/bin/bash

# Script de démarrage pour ChronoTrak avec cron

echo "Démarrage de ChronoTrak..."

# Vérifier l'environnement
FLASK_ENV=${FLASK_ENV:-development}
echo "Environnement détecté : $FLASK_ENV"

# Configurer le cron job seulement en production
if [ "$FLASK_ENV" = "production" ]; then
    echo "Configuration du cron job d'archivage automatique pour la production..."
    
    # Créer le cron job pour l'archivage automatique
    echo "0 2 * * * chronouser cd /app && FLASK_ENV=production flask auto-archive >> /var/log/chronotrak_archive.log 2>&1" > /etc/cron.d/chronotrak-archive
    chmod 0644 /etc/cron.d/chronotrak-archive
    
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
else
    echo "Archivage automatique désactivé en environnement '$FLASK_ENV' (seulement en production)"
fi

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
