import os
import logging
from flask import Flask, jsonify

# Configuração robusta de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'ConcursoIA',
        'timestamp': '2025-10-28'
    })

# Rota principal
@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎯 ConcursoIA - Diagnóstico</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f8ff; }
            .container { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto; }
            h1 { color: #2c3e50; text-align: center; }
            .status { color: #27ae60; font-weight: bold; font-size: 1.2em; }
            .info { background: #e8f4fd; padding: 15px; border-radius: 8px; margin: 15px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 ConcursoIA - Sistema de Diagnóstico</h1>
            <div class="info">
                <p><strong>Status:</strong> <span class="status">Sistema em Diagnóstico</span></p>
                <p><strong>Servidor:</strong> Gunicorn + Docker</p>
                <p><strong>Ambiente:</strong> Produção Railway</p>
            </div>
            <p>Se você está vendo esta mensagem, o sistema está funcionando!</p>
            <p>
                <a href="/health">✅ Health Check</a> | 
                <a href="/test">🧪 Teste Completo</a> |
                <a href="/api/materias">📚 Matérias</a>
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/test')
def test():
    return jsonify({
        'message': 'ConcursoIA - Teste de Diagnóstico',
        'status': 'diagnostic_mode',
        'server': 'gunicorn_docker',
        'endpoints': ['/', '/health', '/test', '/api/materias']
    })

# NÃO HÁ app.run() - O Gunicorn cuida disso em produção
# EM DESENVOLVIMENTO LOCAL, EXECUTE: python app.py
if __name__ == '__main__':
    logger.info('🔧 MODO DESENVOLVIMENTO LOCAL')
    app.run(host='0.0.0.0', port=5001, debug=True)
