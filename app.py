import os
import sqlite3
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Configuração básica
@app.route('/')
def home():
    return '<h1>ConcursoIA - Sistema Online</h1><p>Sistema carregando...</p>'

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Sistema funcionando'})

# SIMULAÇÃO DAS SUAS ROTAS EXISTENTES - ADICIONE AQUI SUAS ROTAS REAIS

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    print(f'🚀 Iniciando servidor na porta {port}')
    app.run(host='0.0.0.0', port=port, debug=debug)
