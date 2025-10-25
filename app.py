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

def init_database_safe():
    '''Inicialização ultra-segura do banco'''
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Criar tabelas se não existirem
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT,
                materia TEXT DEFAULT 'Geral',
                alternativas TEXT,
                resposta_correta TEXT,
                explicacao TEXT
            )
        ''')
        
        # Inserir questões se estiver vazia
        cursor.execute('SELECT COUNT(*) FROM questoes')
        if cursor.fetchone()[0] == 0:
            questões = [
                ('Qual é a capital do Brasil?', 'Geografia', '{"A": "Rio", "B": "Brasilia", "C": "SP", "D": "Salvador"}', 'B', 'Brasilia é a capital'),
                ('Quem escreveu Dom Casmurro?', 'Literatura', '{"A": "Machado", "B": "Alencar", "C": "Assis", "D": "Ramos"}', 'A', 'Machado de Assis')
            ]
            for q in questões:
                cursor.execute('INSERT INTO questoes (enunciado, materia, alternativas, resposta_correta, explicacao) VALUES (?,?,?,?,?)', q)
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    init_database_safe()
    # Sempre retorna matérias, mesmo se o banco falhar
    materias = ['Geografia', 'Literatura', 'Historia', 'Matematica']
    return render_template('simulado.html', materias=materias)

@app.route('/redacao')
def redacao():
    return render_template('redacao.html', tema={'tema': 'Tema Exemplo', 'dicas': 'Escreva sobre...'})

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
