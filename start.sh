#!/bin/bash
echo "🚀 Iniciando ConcursoIA com Gunicorn..."
gunicorn app:app --bind 0.0.0.0:8080 --workers 1 --threads 2 --timeout 120
