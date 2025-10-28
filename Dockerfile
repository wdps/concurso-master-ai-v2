FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

# Tornar start.sh executável
RUN chmod +x start.sh

# Expor porta
EXPOSE 8080

# Comando de inicialização
CMD ["./start.sh"]
