from flask import Flask, jsonify
import os
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎯 ConcursoIA - Gunicorn Production</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; }
            .status { color: #27ae60; font-weight: bold; }
            .warning { color: #e74c3c; background: #ffeaa7; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 ConcursoIA - Sistema Online</h1>
            <div class="warning">
                <strong>⚠️  AVISO:</strong> Se você está vendo esta página, o Railway está IGNORANDO o Dockerfile!
            </div>
            <p>Status: <span class="status">Sistema Carregado</span></p>
            <p>Servidor: <strong>Flask (Modo Desenvolvimento)</strong> ← PROBLEMA!</p>
            <p>Esperado: <strong>Gunicorn (Modo Produção)</strong></p>
            <p>
                <a href="/health">Health Check</a> | 
                <a href="/test">Teste Completo</a>
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({
        'status': 'loaded_but_wrong_server',
        'server': 'flask_development',
        'expected': 'gunicorn_production',
        'message': 'Railway está executando Flask em vez de Gunicorn!'
    })

@app.route('/test')
def test():
    return jsonify({
        'problem': 'railway_ignoring_dockerfile',
        'current_server': 'flask_development',
        'expected_server': 'gunicorn_production',
        'port': 5001,
        'solution': 'Check railway project settings for Dockerfile usage'
    })

# ⚠️ CRÍTICO: NÃO HÁ app.run() - MAS O RAILWAY ESTÁ EXECUTANDO python app.py DIRETO!
# O Railway está IGNORANDO nosso Dockerfile completamente!
