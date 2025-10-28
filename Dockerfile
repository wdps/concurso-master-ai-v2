FROM python:3.11-slim

WORKDIR /app

# Copiar requirements primeiro (para cache de dependências)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

# Inicializar banco de dados
RUN python init_db.py

# Expor porta
EXPOSE 8080

# Comando de inicialização
CMD ["./start.sh"]
