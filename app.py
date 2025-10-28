import os
import sys
from flask import Flask, jsonify
import logging

# Configurar logging para stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    logger.info('Acessando rota /')
    return '<h1>🎯 ConcursoIA - ONLINE</h1><p>Se você vê esta mensagem, está funcionando!</p>'

@app.route('/health')
def health():
    logger.info('Acessando rota /health')
    return jsonify({'status': 'healthy', 'service': 'ConcursoIA'})

@app.route('/test')
def test():
    logger.info('Acessando rota /test')
    return jsonify({'message': 'Teste bem-sucedido!'})

# Se for executado diretamente, apenas para desenvolvimento
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f'Iniciando servidor Flask na porta {port}')
    app.run(host='0.0.0.0', port=port, debug=False)
