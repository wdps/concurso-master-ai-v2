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
        
except Exception as e:
    gemini_error = str(e)
    logger.error(f"❌ Erro ao carregar Gemini: {e}")

# ========== ROTAS BÁSICAS ==========

@app.route('/')
def home():
    return '''<h1>🎯 ConcursoIA - Sistema Online</h1>
    <p>Status: <strong>Operacional</strong></p>
    <p>Gemini: ''' + ('✅ Configurado' if gemini_configured else '❌ Não configurado') + '''</p>
    <p><a href="/health">Health Check</a> | <a href="/test">Teste Completo</a></p>
    <p><a href="/api/materias">Matérias</a> | <a href="/api/redacao/temas">Temas Redação</a></p>'''

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
        'gemini_error': gemini_error
    })

# ========== CONFIGURAÇÃO DO SERVIDOR ==========
# EM PRODUÇÃO NO RAILWAY, O SERVIDOR É INICIADO VIA GUNICORN
# NÃO EXECUTAR app.run() - O RAILWAY FAZ ISSO AUTOMATICAMENTE

# NOTA: O Railway está executando este arquivo diretamente, então
# não devemos ter o bloco if __name__ == '__main__' em produção
