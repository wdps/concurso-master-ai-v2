FROM python:3.11-slim

WORKDIR /app

# Instalar curl para health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

# Expor porta
EXPOSE 8080

# Script de inicialização que DETECTA se está sendo usado
RUN echo '#!/bin/bash' > /app/start.sh
RUN echo 'echo "🚀 DOCKERFILE EXECUTADO - INICIANDO GUNICORN..."' >> /app/start.sh
RUN echo 'echo "📊 Porta: \5001"' >> /app/start.sh
RUN echo 'echo "🔧 Iniciando Gunicorn..."' >> /app/start.sh
RUN echo 'exec gunicorn app:app --bind 0.0.0.0:8080 --workers 1 --threads 2 --timeout 120 --access-logfile - --error-logfile -' >> /app/start.sh
RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando principal
CMD ["/app/start.sh"]
