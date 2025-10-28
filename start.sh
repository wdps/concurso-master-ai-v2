#!/bin/bash
echo "🚀 Iniciando ConcursoIA..."
echo "📊 Porta: 5001"
echo "🐍 Python: Python 3.13.2"
echo "📦 Instalando dependências..."
pip install -r requirements.txt

echo "🔧 Iniciando Gunicorn..."
exec gunicorn --bind 0.0.0.0:5001 --workers 1 --threads 2 --timeout 120 --access-logfile - --error-logfile - app:app
