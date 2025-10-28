# Usar Python 3.11, que é estável e recomendado
FROM python:3.11-slim

# Definir o diretório de trabalho
WORKDIR /app

# Copiar apenas o requirements.txt primeiro para cachear as dependências
COPY requirements.txt .

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o resto do projeto (app.py, static/, templates/, concursos.db)
COPY . .

# Criar o script de inicialização que usa a porta do Railway (\5001)
RUN echo '#!/bin/bash' > /app/start.sh
RUN echo 'echo "--- 🚀 INICIANDO SERVIDOR GUNICORN NA PORTA \5001 ---"' >> /app/start.sh
RUN echo 'exec gunicorn app:app --bind 0.0.0.0:\5001 --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile -' >> /app/start.sh
RUN chmod +x /app/start.sh

# Comando final para iniciar o servidor
CMD ["/app/start.sh"]
