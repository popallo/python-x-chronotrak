FROM python:3.11-alpine

# Accepter la version comme argument de build
ARG VERSION=dev

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLASK_APP=run.py \
    FLASK_ENV=production \
    TZ=Europe/Paris

# Installer bash, cron, curl et les dépendances système
RUN apk add --no-cache bash tzdata dcron curl && \
    addgroup -S chronouser && \
    adduser -S -G chronouser chronouser

# Créer le répertoire de l'application
WORKDIR /app

# Copier uniquement les fichiers de dépendances d'abord
COPY pyproject.toml .

# Installer les dépendances Python dans une couche séparée
RUN pip install --no-cache-dir -e . && \
    pip install --upgrade setuptools>=70.0.0

# Copier les fichiers de l'application
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY management/ ./management/
COPY config.py run.py wsgi.py start.sh ./

# Créer le fichier VERSION avec la valeur fournie
RUN echo -n "$VERSION" > ./app/VERSION

# Ajouter des métadonnées à l'image
LABEL org.opencontainers.image.title="ChronoTrak" \
      org.opencontainers.image.description="Application de gestion de crédit-temps client" \
      org.opencontainers.image.version="$VERSION" \
      org.opencontainers.image.vendor="apacher.eu" \
      org.opencontainers.image.url="https://chronotrak.fr" \
      org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# Créer le répertoire instance et définir les permissions
RUN mkdir -p /app/instance /var/log /app/logs && \
    chown -R chronouser:chronouser /app && \
    chmod -R 755 /app && \
    chmod 777 /app/instance && \
    chmod 755 /app/logs && \
    chmod +x /app/management/setup_cron.sh && \
    chmod +x /app/start.sh && \
    chown chronouser:chronouser /var/log

# Configurer le cron job pour l'archivage automatique (seulement en production)
# Le cron job sera créé conditionnellement dans le script de démarrage

# Passer à l'utilisateur non-root
USER chronouser

# Ajouter un healthcheck pour vérifier la santé du conteneur
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

CMD ["./start.sh"]