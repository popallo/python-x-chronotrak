FROM python:3.13-alpine

# Accepter la version comme argument de build
ARG VERSION=dev

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py \
    FLASK_ENV=production \
    TZ=Europe/Paris \
    PYTHON_JIT=1 \
    PYTHONOPTIMIZE=1 \
    PYTHONHASHSEED=0 \
    PYTHONMALLOC=malloc \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Installer bash, cron, curl, uv et les dépendances système
RUN apk add --no-cache bash tzdata dcron curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    addgroup -S chronouser && \
    adduser -S -G chronouser chronouser

WORKDIR /app

# Copier les fichiers de dépendances d'abord (cache Docker)
COPY pyproject.toml uv.lock ./

# Installer les dépendances Python sans le projet (couche cacheable)
RUN uv venv && uv sync --frozen --no-dev --no-install-project

# Copier les fichiers de l'application
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY management/ ./management/
COPY config.py run.py wsgi.py start.sh ./
COPY RELEASE_NOTES.yaml ./

# Installer le projet et finaliser l'environnement
RUN uv sync --frozen --no-dev

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

# Passer à l'utilisateur non-root
USER chronouser

# Ajouter un healthcheck pour vérifier la santé du conteneur
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

CMD ["./start.sh"]
