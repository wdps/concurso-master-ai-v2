FROM python:3.11-slim

WORKDIR /app

# Copiar requirements primeiro (para cache de dependências)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

# Tornar start.sh executável (comando Unix)
RUN chmod +x start.sh

# Expor porta
EXPOSE 8080

# Comando de inicialização - duas opções:
# Opção 1: Usar start.sh (vamos tentar primeiro)
CMD ["./start.sh"]

# Opção 2: Comando direto (descomente se a opção 1 falhar)
# CMD ["python", "app.py"]
