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
except ImportError as e:
    gemini_error = str(e)
    logger.error(f"❌ Erro ao carregar Google Generative AI: {e}")
except Exception as e:
    gemini_error = str(e)
    logger.error(f"❌ Erro inesperado ao carregar Gemini: {e}")

# Configurar Gemini se disponível
if gemini_configured:
    try:
        # Verificar se a chave de API está disponível
        api_key = os.environ.get('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            logger.info("✅ Gemini configurado com sucesso!")
        else:
            logger.warning("⚠️  GEMINI_API_KEY não encontrada. Gemini não configurado.")
            gemini_configured = False
    except Exception as e:
        gemini_error = str(e)
        logger.error(f"❌ Erro ao configurar Gemini: {e}")
        gemini_configured = False

# Rotas básicas
@app.route('/')
def home():
    status = {
        'app': 'ConcursoIA',
        'status': 'online',
        'gemini_configured': gemini_configured,
        'gemini_error': gemini_error,
        'timestamp': time.time()
    }
    return jsonify(status)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

@app.route('/test')
def test():
    return jsonify({
        'message': 'ConcursoIA funcionando!',
        'gemini': 'configured' if gemini_configured else f'error: {gemini_error}',
        'python_version': os.environ.get('PYTHON_VERSION', 'unknown')
    })

# Configuração do servidor
PORT = int(os.environ.get('PORT', 5001))
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

if __name__ == '__main__':
    logger.info(f'🚀 Iniciando ConcursoIA na porta {PORT}')
    logger.info(f'📊 Gemini configurado: {gemini_configured}')
    if gemini_error:
        logger.info(f'⚠️  Erro Gemini: {gemini_error}')
    
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
