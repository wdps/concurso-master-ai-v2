#!/usr/bin/env python3
"""
Ponto de entrada para produção - usa Gunicorn
"""
import os
from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f'🚀 Iniciando ConcursoIA na porta {port} com Gunicorn')
    # Este arquivo é usado pelo Gunicorn, não inicia servidor Flask
