from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import random
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'concurso_master_ai_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

def get_db_connection():
    conn = sqlite3.connect('concurso.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enunciado TEXT,
            materia TEXT,
            alternativas TEXT,
            resposta_correta TEXT,
            explicacao TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temas_redacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema TEXT,
            categoria TEXT,
            dicas TEXT
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM temas_redacao')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO temas_redacao (tema, categoria, dicas) VALUES (?, ?, ?)', 
                      ('Tema exemplo', 'Geral', 'Escreva sobre este tema'))
    
    conn.commit()
    conn.close()
    return True

@app.route('/')
def index():
    return 'ConcursoMaster AI - Online!'

@app.route('/simulado')
def simulado():
    return render_template('simulado.html')

@app.route('/redacao')
def redacao():
    init_database()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM temas_redacao LIMIT 1')
    tema = cursor.fetchone()
    conn.close()
    
    tema_dict = dict(tema) if tema else {'tema': 'Tema padrao', 'categoria': 'Geral', 'dicas': 'Dicas aqui'}
    return render_template('redacao.html', tema=tema_dict)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/health')
def health():
    return {'status': 'online', 'message': 'ConcursoMaster AI funcionando'}

@app.route('/api/questoes/random')
def get_questoes():
    try:
        init_database()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM questoes LIMIT 5')
        questao_list = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        for q in questao_list:
            try:
                q['alternativas'] = json.loads(q['alternativas'])
            except:
                q['alternativas'] = {'A': 'Alt A', 'B': 'Alt B', 'C': 'Alt C', 'D': 'Alt D'}
        
        return jsonify({'questoes': questao_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
