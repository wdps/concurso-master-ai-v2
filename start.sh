#!/bin/bash
# start.sh - Script alternativo de inicialização

echo "🚀 Iniciando ConcursoMaster AI..."

# Verificar se o Gunicorn está instalado
if ! command -v gunicorn &> /dev/null; then
    echo "❌ Gunicorn não encontrado, usando Flask diretamente..."
    python app.py
else
    echo "✅ Gunicorn encontrado, iniciando servidor..."
    gunicorn --bind 0.0.0.0: app:app
fi
