from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>🚀 ConcursoIA - TESTE ONLINE</h1><p>Se esta mensagem aparece, o sistema está funcionando!</p>'

@app.route('/health')
def health():
    return jsonify({'status': 'online', 'service': 'ConcursoIA'})

@app.route('/test')
def test():
    return jsonify({'message': 'Sistema operacional', 'timestamp': '2025-10-28'})

# SEM app.run() - O Railway/Gunicorn cuida disso
