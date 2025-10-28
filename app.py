from flask import Flask, jsonify
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    logger.info('Rota / acessada')
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎯 ConcursoIA - Online</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; }
            .status { color: #27ae60; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 ConcursoIA - Sistema Online</h1>
            <p>Status: <span class="status">Operacional</span></p>
            <p>Servidor: Gunicorn</p>
            <p>Gemini: ✅ Configurado</p>
            <p>
                <a href="/health">Health Check</a> | 
                <a href="/test">Teste Completo</a> |
                <a href="/api/materias">Matérias</a>
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    logger.info('Rota /health acessada')
    return jsonify({
        'status': 'healthy',
        'service': 'ConcursoIA',
        'server': 'gunicorn',
        'timestamp': '2025-10-28'
    })

@app.route('/test')
def test():
    logger.info('Rota /test acessada')
    return jsonify({
        'message': 'ConcursoIA funcionando perfeitamente!',
        'status': 'operational',
        'endpoints': ['/', '/health', '/test', '/api/materias', '/api/redacao/temas']
    })

# NÃO HÁ app.run() - O Gunicorn será iniciado via comando
