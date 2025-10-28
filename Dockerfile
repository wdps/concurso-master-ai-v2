FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

# Expor porta
EXPOSE 8080

# Comando DIRETO para Gunicorn - sem scripts intermediários
CMD gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 2 --timeout 120 --access-logfile - --error-logfile - app:app
