import os
import sqlite3
from flask import Flask, render_template, jsonify, request
import logging
import time

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variável global para Gemini
gemini_configured = False
gemini_error = None

# Tentar carregar Gemini de forma segura
try:
    logger.info("🔄 Tentando carregar Google Generative AI...")
    import google.generativeai as genai
    gemini_configured = True
    logger.info("✅ Google Generative AI carregado com sucesso!")
    
    # Configurar Gemini se disponível
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
        logger.info("✅ Gemini configurado com sucesso!")
    else:
        logger.warning("⚠️  GEMINI_API_KEY não encontrada. Gemini não configurado.")
        gemini_configured = False
        
except ImportError as e:
    gemini_error = str(e)
    logger.error(f"❌ Erro ao carregar Google Generative AI: {e}")
except Exception as e:
    gemini_error = str(e)
    logger.error(f"❌ Erro inesperado ao carregar Gemini: {e}")

# ========== ROTAS BÁSICAS ==========

@app.route('/')
def home():
    return '''<h1>🎯 ConcursoIA - Sistema Online</h1>
    <p>Status: <strong>Operacional</strong></p>
    <p>Gemini: ''' + ('✅ Configurado' if gemini_configured else '❌ Não configurado') + '''</p>
    <p><a href="/health">Health Check</a> | <a href="/test">Teste Completo</a></p>'''

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'service': 'ConcursoIA',
        'timestamp': time.time(),
        'gemini_configured': gemini_configured
    })

@app.route('/test')
def test():
    return jsonify({
        'message': 'ConcursoIA funcionando perfeitamente!',
        'status': 'operational',
        'gemini_configured': gemini_configured,
        'gemini_error': gemini_error,
        'python_version': os.environ.get('PYTHON_VERSION', 'unknown'),
        'port': os.environ.get('PORT', '5001')
    })

# ========== CONFIGURAÇÃO DO SERVIDOR ==========
# NÃO INICIAR SERVIDOR FLASK EM PRODUÇÃO - O GUNICORN CUIDA DISSO

# Apenas para desenvolvimento local
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5001))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f'🚀 Iniciando ConcursoIA em modo desenvolvimento')
    logger.info(f'📊 Gemini configurado: {gemini_configured}')
    
    if gemini_error:
        logger.info(f'⚠️  Erro Gemini: {gemini_error}')
    
    # Apenas executar se não estiver no Railway
    if not os.environ.get('RAILWAY_ENVIRONMENT'):
        app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
    else:
        logger.info('🌐 Ambiente Railway detectado - Gunicorn cuidará do servidor')

# Deploy: 2025-10-27 23:11:22

